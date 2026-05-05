import digitalio
import board
import pwmio
import pulseio
from analogio import AnalogIn
import time

OBSTAKEL_DREMPEL_CM = 6

VOLLE_SNELHEID     = 1.0   # 100%
CORRECTIE_SNELHEID = 0.3
DRAAI_SNELHEID     = 0.8


def _snelheid_naar_duty(snelheid: float) -> int:
    """Zet een snelheid (0.0–1.0) om naar een 16-bit duty cycle waarde."""
    snelheid = max(0.0, min(1.0, snelheid))
    return int(snelheid * 65535)


class Rijder:
    def __init__(self, stappenmotor, log=None):
        self.log = log or print
        self.stappenmotor = stappenmotor
        self.noodstop_actief = False
        self.obstakel_actief = False

        # --- Motor pinnen ---
        # Richting: digitale uitgang (True = achteruit, False = vooruit)
        self.right_direction = digitalio.DigitalInOut(board.GP0)
        self.right_direction.direction = digitalio.Direction.OUTPUT
        self.left_direction  = digitalio.DigitalInOut(board.GP2)
        self.left_direction.direction  = digitalio.Direction.OUTPUT

        # Snelheid: PWM uitgang op de enable/power pin
        self.right_pwm = pwmio.PWMOut(board.GP1, frequency=1000, duty_cycle=0)
        self.left_pwm  = pwmio.PWMOut(board.GP3, frequency=1000, duty_cycle=0)

        # --- Lijnvolg sensoren ---
        self.meetpin_rechts_voor = AnalogIn(board.GP28)
        self.meetpin_links_voor  = AnalogIn(board.GP27)
        self.meetpin_achter      = AnalogIn(board.GP26)

        # --- Ultrasone afstandssensor ---
        self._trig = digitalio.DigitalInOut(board.GP16)
        self._trig.direction = digitalio.Direction.OUTPUT
        self._trig.value = False

        self._echo = pulseio.PulseIn(board.GP17, maxlen=1, idle_state=False)
        self._echo.pause()

        # --- Noodstop ---
        self.noodstop_knop = digitalio.DigitalInOut(board.GP22)
        self.noodstop_knop.direction = digitalio.Direction.INPUT
        self.noodstop_knop.pull = digitalio.Pull.UP

        # --- LEDs ---
        self.led_blauw = digitalio.DigitalInOut(board.GP20)
        self.led_groen = digitalio.DigitalInOut(board.GP19)
        self.led_rood  = digitalio.DigitalInOut(board.GP18)

        for led in (self.led_blauw, self.led_groen, self.led_rood):
            led.direction = digitalio.Direction.OUTPUT
            led.value = False

        self.huidige_tijd = time.monotonic()


    def calculate_voltage(self, value):
        return (value * 3.3) / 65535

    def _set_motor(self, kant, snelheid: float, achteruit: bool = False):
        """
        Stel één motor in.
        kant     : 'links' of 'rechts'
        snelheid : 0.0 – 1.0
        achteruit: True = achteruit rijden
        """
        duty = _snelheid_naar_duty(snelheid)
        if kant == 'rechts':
            self.right_direction.value = achteruit
            self.right_pwm.duty_cycle  = duty
        else:
            self.left_direction.value = achteruit
            self.left_pwm.duty_cycle  = duty

    def _stop_motor(self, kant):
        """Zet één motor op 0% duty cycle (stop, geen harde digital False nodig)."""
        if kant == 'rechts':
            self.right_pwm.duty_cycle = 0
        else:
            self.left_pwm.duty_cycle = 0

    def obstakel_gedetecteerd(self):
        # Stuur trigger-puls van 10 µs
        self._trig.value = False
        time.sleep(0.000002)
        self._trig.value = True
        time.sleep(0.00001)
        self._trig.value = False

        # Meet echo-puls
        self._echo.clear()
        self._echo.resume()
        time.sleep(0.03)
        self._echo.pause()

        if not self._echo:
            return False  # buiten bereik, geen obstakel

        duration_us = self._echo[0]
        afstand_cm = (duration_us * 0.0343) / 2

        self.log(f"Afstand: {afstand_cm:.1f} cm")

        if afstand_cm < OBSTAKEL_DREMPEL_CM:
            self.stop()
            self.zet_led(blauw=False, groen=False, rood=True)
            self.obstakel_actief = True
            self.log("OBSTAKEL GEDETECTEERD")
            return True

        return False

    def zet_led(self, blauw=False, groen=False, rood=False):
        self.led_blauw.value = blauw
        self.led_groen.value = groen
        self.led_rood.value  = rood


    def stop(self):
        self._stop_motor('rechts')
        self._stop_motor('links')

    def rijd_vooruit(self, correctie_tijd=None):
        self._set_motor('rechts', 0.5, achteruit=False)
        self._set_motor('links',  0.5, achteruit=False)
        time.sleep(0.2)

        while (self.calculate_voltage(self.meetpin_achter.value) < 0.5
               or (time.monotonic() - self.huidige_tijd) < 0.5):

            if self.noodstop_gedetecteerd() or self.obstakel_gedetecteerd():
                self.rijder.stop()
                return  # stop() is al aangeroepen binnen obstakel_gedetecteerd()

            links_v  = self.calculate_voltage(self.meetpin_links_voor.value)
            rechts_v = self.calculate_voltage(self.meetpin_rechts_voor.value)

            links_op_lijn  = links_v  > 0.5
            rechts_op_lijn = rechts_v > 0.5

            if links_op_lijn and rechts_op_lijn:
                self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)

            elif not links_op_lijn and rechts_op_lijn:
                self._set_motor('rechts', CORRECTIE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID,     achteruit=False)

            elif links_op_lijn and not rechts_op_lijn:
                self._set_motor('rechts', VOLLE_SNELHEID,     achteruit=False)
                self._set_motor('links',  CORRECTIE_SNELHEID, achteruit=False)

            else:
                self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)

            if correctie_tijd:
                if time.monotonic() - self.huidige_tijd >= correctie_tijd:
                    break
            time.sleep(0.01)

        self.log("over kruispunt gekomen nog beetje vooruit aan het rijden")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)
        if correctie_tijd is None:
            time.sleep(0.3)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def rijd_achteruit(self):
        self.log("achteruit aan het rijden")
        self._set_motor('rechts', 0.5, achteruit=True)
        self._set_motor('links',  0.5, achteruit=True)
        time.sleep(0.2)

        while (self.calculate_voltage(self.meetpin_achter.value) < 0.5
            or (time.monotonic() - self.huidige_tijd) < 0.3):

            if self.noodstop_gedetecteerd() or self.obstakel_gedetecteerd():
                self.rijder.stop()
                return

            links_v  = self.calculate_voltage(self.meetpin_links_voor.value)
            rechts_v = self.calculate_voltage(self.meetpin_rechts_voor.value)

            links_op_lijn  = links_v  > 0.5
            rechts_op_lijn = rechts_v > 0.5

            if links_op_lijn and rechts_op_lijn:
                self._set_motor('rechts', DRAAI_SNELHEID, achteruit=True)
                self._set_motor('links',  DRAAI_SNELHEID, achteruit=True)

            elif not links_op_lijn and rechts_op_lijn:
                self._set_motor('rechts', DRAAI_SNELHEID,     achteruit=True)
                self._set_motor('links',  CORRECTIE_SNELHEID, achteruit=True)

            elif links_op_lijn and not rechts_op_lijn:
                self._set_motor('rechts', CORRECTIE_SNELHEID, achteruit=True)
                self._set_motor('links',  DRAAI_SNELHEID,     achteruit=True)

            else:
                self._set_motor('rechts', DRAAI_SNELHEID, achteruit=True)
                self._set_motor('links',  DRAAI_SNELHEID, achteruit=True)

            time.sleep(0.01)

        self.huidige_tijd = time.monotonic()
        self.stop()

    def draai_links(self):
        self.log("Links aan het draaien")
        self._set_motor('rechts', 0.9, achteruit=False)
        self._set_motor('links',  0.9, achteruit=True)
        time.sleep(0.6)
        self._set_motor('rechts', 0.4, achteruit=False)
        self._set_motor('links',  0.4, achteruit=True)
        while self.calculate_voltage(self.meetpin_links_voor.value) < 0.5:
            if self.noodstop_gedetecteerd() or self.obstakel_gedetecteerd():
                self.rijder.stop()
                return
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met links draaien")
        self.log("LDR links:"  + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()

    def draai_rechts(self):
        self.log("Rechts aan het draaien")
        self._set_motor('rechts', 1,   achteruit=True)
        self._set_motor('links',  0.8, achteruit=False)
        time.sleep(0.6)
        self._set_motor('rechts', 0.4, achteruit=True)
        self._set_motor('links',  0.3, achteruit=False)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) < 0.5:
            if self.noodstop_gedetecteerd() or self.obstakel_gedetecteerd():
                self.rijder.stop()
                return
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met rechts draaien")
        self.log("LDR links:"  + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()


    def positioneer_toren(self):
        self.zet_led(blauw=False, groen=True, rood=False)
        self.stop()
        time.sleep(0.5)

        self.huidige_tijd = time.monotonic()
        self.rijd_vooruit(1)
        time.sleep(0.2)

        self.huidige_tijd = time.monotonic()
        self.rijd_achteruit()
        time.sleep(0.2)

        self.huidige_tijd = time.monotonic()
        self.rijd_vooruit(0.75)
        self.stappenmotor.plaats_toren()


    def noodstop_gedetecteerd(self):
        if self.noodstop_knop.value:
            self.log("NOODSTOP ingedrukt!")
            self.zet_led(blauw=False, groen=False, rood=True)
            self.stop()
            return True
        return False