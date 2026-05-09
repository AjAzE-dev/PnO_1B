import digitalio
import board
import pwmio
import pulseio
from us100_pio import US100PIO
from analogio import AnalogIn
import time
import math

OBSTAKEL_DREMPEL_CM = 6.7
OBSTAKEL_MIN_CM     = 3   # metingen onder deze waarde zijn ruis

VOLLE_SNELHEID     = 1.0   # 100%
CORRECTIE_SNELHEID = 0.3
DRAAI_SNELHEID     = 0.8

LED_CYCLUS_PERIODE = 1.0  # seconden per cyclus


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
        self.websocket_stop  = False
        self._noodstop_sinds = None

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

        self.begin_time = 0

        # --- Noodstop ---
        self.noodstop_knop = digitalio.DigitalInOut(board.GP22)
        self.noodstop_knop.direction = digitalio.Direction.INPUT
        self.noodstop_knop.pull = None

        # --- LEDs (PWM voor kleurmenging) ---
        self.led_rood  = pwmio.PWMOut(board.GP5,  frequency=1000, duty_cycle=0)
        self.led_groen = pwmio.PWMOut(board.GP4,  frequency=1000, duty_cycle=0)
        self.led_blauw = pwmio.PWMOut(board.GP14, frequency=1000, duty_cycle=0)

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

    def zet_led_rgb(self, r: int = 0, g: int = 0, b: int = 0):
        """Stel LED-kleur in met RGB-waarden (0-255)."""
        self.led_rood.duty_cycle  = int(r / 255 * 65535)
        self.led_groen.duty_cycle = int(g / 255 * 65535)
        self.led_blauw.duty_cycle = int(b / 255 * 65535)

    def zet_led(self, blauw=False, groen=False, rood=False):
        """Achterwaartse compatibiliteit: aan/uit per kleur."""
        self.zet_led_rgb(
            r=255 if rood  else 0,
            g=255 if groen else 0,
            b=255 if blauw else 0,
        )

    def _update_led_cyclus(self, modus: str):
        """
        Niet-blokkerende LED-update. Roep aan in rijlussen.
        modus: 'wit_groen_sinus' | 'oranje_cyclus' | 'rood_cyclus'
        """
        t = time.monotonic()
        if modus == 'wit_groen_sinus':
            # RGB(t) = (L(t), 1, L(t)) met L(t) = 0.5 + 0.5*sin(2*pi*t)
            L = 0.5 + 0.5 * math.sin(2 * math.pi * t)
            self.zet_led_rgb(int(L * 255), 255, int(L * 255))
        elif modus == 'oranje_cyclus':
            aan = (t % LED_CYCLUS_PERIODE) < (LED_CYCLUS_PERIODE / 2)
            self.zet_led_rgb(255, 20, 0) if aan else self.zet_led_rgb(0, 0, 0)
        elif modus == 'rood_cyclus':
            aan = (t % LED_CYCLUS_PERIODE) < (LED_CYCLUS_PERIODE / 2)
            self.zet_led_rgb(255, 0, 0) if aan else self.zet_led_rgb(0, 0, 0)

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

        # Negeer metingen onder OBSTAKEL_MIN_CM als ruis
        if afstand_cm < OBSTAKEL_MIN_CM:
            return False

        if afstand_cm < OBSTAKEL_DREMPEL_CM:
            self.stop()
            self.obstakel_actief = True
            self.log("OBSTAKEL GEDETECTEERD")
            return True

        return False

    def stop(self):
        self._stop_motor('rechts')
        self._stop_motor('links')

    def rijd_vooruit(self, correctie_tijd=None):
        self._set_motor('rechts', 0.5, achteruit=False)
        self._set_motor('links',  0.5, achteruit=False)
        time.sleep(0.2)

        while (self.calculate_voltage(self.meetpin_achter.value) < 0.5
               or (time.monotonic() - self.huidige_tijd) < 0.5):

            self._update_led_cyclus('wit_groen_sinus')  # wit+groen sinuscyclus

            if self.moet_stoppen():
                self.zet_led_rgb(0, 0, 0)
                return
            if ((self.obstakel_gedetecteerd() and time.monotonic() - self.begin_time > 1) or self.moet_stoppen()):
                self.zet_led_rgb(0, 0, 0)
                self.stop()
                return

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
        self.zet_led_rgb(0, 0, 0)
        self.stop()

    def rijd_achteruit(self):
        self.log("achteruit aan het rijden")
        self._set_motor('rechts', 0.6, achteruit=True)
        self._set_motor('links',  0.5, achteruit=True)
        time.sleep(0.2)

        while (self.calculate_voltage(self.meetpin_achter.value) < 0.5
            or (time.monotonic() - self.huidige_tijd) < 0.3):

            self._update_led_cyclus('rood_cyclus')  # rood aan-uit cyclus

            if self.moet_stoppen():
                self.zet_led_rgb(0, 0, 0)
                return
            if self.obstakel_gedetecteerd() or self.moet_stoppen():
                self.zet_led_rgb(0, 0, 0)
                return
            time.sleep(0.01)

        self.huidige_tijd = time.monotonic()
        self.zet_led_rgb(0, 0, 0)
        self.stop()

    def draai_links(self):
        self.log("Links aan het draaien")
        self._set_motor('rechts', 0.9, achteruit=False)
        self._set_motor('links',  0.9, achteruit=True)
        time.sleep(0.6)
        self._set_motor('rechts', 0.4, achteruit=False)
        self._set_motor('links',  0.4, achteruit=True)
        while self.calculate_voltage(self.meetpin_links_voor.value) < 0.5:
            if self.moet_stoppen():
                self.zet_led_rgb(0, 0, 0)
                return
            if self.obstakel_gedetecteerd() or self.moet_stoppen():
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
        self._set_motor('links',  0.6, achteruit=False)
        time.sleep(0.6)
        self._set_motor('rechts', 0.4, achteruit=True)
        self._set_motor('links',  0.3, achteruit=False)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) < 0.5:
            if self.moet_stoppen():
                self.zet_led_rgb(0, 0, 0)
                return
            if self.obstakel_gedetecteerd() or self.moet_stoppen():
                return
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met rechts draaien")
        self.log("LDR links:"  + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()

    def positioneer_toren(self):
        self.huidige_tijd = time.monotonic()
        self.rijd_vooruit(1)
        time.sleep(0.2)

        self.huidige_tijd = time.monotonic()
        self.rijd_achteruit()
        time.sleep(0.2)

        self.huidige_tijd = time.monotonic()
        self.rijd_vooruit(0.75)
        time.sleep(0.3)
        self.zet_led_rgb(255, 20, 0)   # oranje constant tijdens plaatsen toren
        self.stappenmotor.plaats_toren()
        self.zet_led_rgb(0, 0, 0)

    def noodstop_gedetecteerd(self):
        if self.noodstop_knop.value:
            if self._noodstop_sinds is None:
                self._noodstop_sinds = time.monotonic()
            elif time.monotonic() - self._noodstop_sinds >= 0.05:
                self.log("NOODSTOP ingedrukt!")
                self.stop()
                self.noodstop_actief = True
                return True
        else:
            self._noodstop_sinds = None
        return False
    
    def moet_stoppen(self):
        if self.websocket_stop:
            self.stop()
            self.zet_led_rgb(0, 0, 0)
            return True
        return self.noodstop_gedetecteerd()