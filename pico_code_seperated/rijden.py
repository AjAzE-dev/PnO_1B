import digitalio
import board
import pwmio
from analogio import AnalogIn
import time

OBSTAKEL_DREMPEL_CM = 7

VOLLE_SNELHEID    = 1.0   # 100%
CORRECTIE_SNELHEID = 0.5  # 60% — trager wiel bij zachte correctie


def _snelheid_naar_duty(snelheid: float) -> int:
    """Zet een snelheid (0.0–1.0) om naar een 16-bit duty cycle waarde."""
    snelheid = max(0.0, min(1.0, snelheid))
    return int(snelheid * 65535)


class Rijder:
    def __init__(self, stappenmotor, log=None):
        self.log = log or print
        self.stappenmotor = stappenmotor
        self.noodstop_actief = False

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

        # --- Ultrasone sensor (US-100) ---
        # uart = busio.UART(board.GP4, board.GP5, baudrate=9600)
        # self.us100 = adafruit_us100.US100(uart)

        # --- Noodstop knop ---
        '''
        self.noodstop_knop = digitalio.DigitalInOut(board.GP22)
        self.noodstop_knop.direction = digitalio.Direction.INPUT
        self.noodstop_knop.pull = digitalio.Pull.UP
        '''

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

    '''
    def obstakel_gedetecteerd(self):
        try:
            afstand = self.us100.distance
            return afstand is not None and afstand < OBSTAKEL_DREMPEL_CM
        except Exception:
            return False
    '''

    def stop(self):
        self._stop_motor('rechts')
        self._stop_motor('links')

    def rijd_vooruit(self, extra_tijd=None):
        while (self.calculate_voltage(self.meetpin_achter.value) < 0.5
               or (time.monotonic() - self.huidige_tijd) < 0.3):

            links_v  = self.calculate_voltage(self.meetpin_links_voor.value)
            rechts_v = self.calculate_voltage(self.meetpin_rechts_voor.value)

            links_op_lijn  = links_v  > 0.5
            rechts_op_lijn = rechts_v > 0.5

            if links_op_lijn and rechts_op_lijn:
                # Beide op lijn → volle snelheid
                self.log("correct vooruit aan het rijden LDR achter:"
                         + str(self.calculate_voltage(self.meetpin_achter.value)))
                self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)

            elif not links_op_lijn and rechts_op_lijn:
                # Te ver naar rechts gedraaid → links vol, rechts traag om zacht naar links te corrigeren
                self.log("links niet op lijn — zacht corrigeren naar links")
                self.log("LDR links:"  + str(links_v))
                self.log("LDR rechts:" + str(rechts_v))
                self._set_motor('rechts', CORRECTIE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID,     achteruit=False)

            elif links_op_lijn and not rechts_op_lijn:
                # Te ver naar links gedraaid → rechts vol, links traag om zacht naar rechts te corrigeren
                self.log("rechts niet op lijn — zacht corrigeren naar rechts")
                self.log("LDR links:"  + str(links_v))
                self.log("LDR rechts:" + str(rechts_v))
                self._set_motor('rechts', VOLLE_SNELHEID,     achteruit=False)
                self._set_motor('links',  CORRECTIE_SNELHEID, achteruit=False)

            else:
                # Beide sensoren missen de lijn (kruispunt of volledig naast) → rechtdoor
                self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
                self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)

            time.sleep(0.01)

        self.log("over kruispunt gekomen nog beetje vooruit aan het rijden")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)
        time.sleep(0.3)
        if extra_tijd:
            time.sleep(extra_tijd)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def rijd_achteruit(self):
        self.log("achteruit aan het rijden")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=True)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=True)
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_achter.value) < 0.5:
            time.sleep(0.1)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def draai_links(self):
        self.log("Links aan het draaien")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=True)
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_links_voor.value) < 0.5:
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met links draaien")
        self.log("LDR links:"  + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()

    def draai_rechts(self):
        self.log("Rechts aan het draaien")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=True)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) < 0.5:
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met rechts draaien")
        self.log("LDR links:"  + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()
    
    def rijd_vooruit_tijd(self, seconden):
        
        self.log("Vooruit rijden voor " + str(seconden) + "s (tijdgebaseerd)")
        self._set_motor('rechts', VOLLE_SNELHEID, achteruit=False)
        self._set_motor('links',  VOLLE_SNELHEID, achteruit=False)
        time.sleep(seconden)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def positioneer_toren(self):
        self.stop()
        time.sleep(2)
        self.stappenmotor.plaats_toren()

    """
    def noodstop_gedetecteerd(self):
        if not self.noodstop_knop.value:
            self.noodstop_actief = True
            self.log("NOODSTOP ingedrukt!")
            self.stop()
            return True
        return False
    """