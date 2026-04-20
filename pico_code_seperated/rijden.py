import digitalio
import board
import busio
import adafruit_us100
from analogio import AnalogIn
from adafruit_httpserver import Server, Request, Response, GET, Websocket
import time

OBSTAKEL_DREMPEL_CM = 7

class Rijder:
    def __init__(self, stappenmotor, log=None):
        self.log = log or print
        self.stappenmotor = stappenmotor
        self.noodstop_actief = False

        
        # --- Motor pinnen ---
        self.right_power = digitalio.DigitalInOut(board.GP1)
        self.right_power.direction = digitalio.Direction.OUTPUT
        self.right_direction = digitalio.DigitalInOut(board.GP0)
        self.right_direction.direction = digitalio.Direction.OUTPUT
        self.left_power = digitalio.DigitalInOut(board.GP3)
        self.left_power.direction = digitalio.Direction.OUTPUT
        self.left_direction = digitalio.DigitalInOut(board.GP2)
        self.left_direction.direction = digitalio.Direction.OUTPUT

        # --- Lijnvolg sensoren ---
        self.meetpin_rechts_voor = AnalogIn(board.GP28)
        self.meetpin_links_voor  = AnalogIn(board.GP27)
        self.meetpin_achter      = AnalogIn(board.GP26)

        # --- Ultrasone sensor (US-100) ---
        #uart = busio.UART(board.GP4, board.GP5, baudrate=9600)
        #self.us100 = adafruit_us100.US100(uart)
        
         # --- Noodstop knop ---
        ''' 
        self.noodstop_knop = digitalio.DigitalInOut(board.GP22)
        self.noodstop_knop.direction = digitalio.Direction.INPUT
        self.noodstop_knop.pull = digitalio.Pull.UP
        '''

        self.huidige_tijd = time.monotonic()

    def calculate_voltage(self, value):
        return (value * 3.3) / 65535

    '''
    def obstakel_gedetecteerd(self):
        try:
            afstand = self.us100.distance
            return afstand is not None and afstand < OBSTAKEL_DREMPEL_CM
        except Exception:
            return False
    '''
    

    def stop(self):
        self.right_power.value = False
        self.left_power.value  = False

    def rijd_vooruit(self, extra_tijd=None):
        self.right_power.value = True
        self.left_power.value  = True
        self.left_direction.value  = False
        self.right_direction.value  = False
        '''
        while self.calculate_voltage(self.meetpin_achter.value) < 0.45 or  (time.monotonic() - self.huidige_tijd) < 0.3:
            if self.noodstop_gedetecteerd() :#or self.obstakel_gedetecteerd():
                self.log("obstakel gedecteerd of noodstop ingeduwd")
                self.stop()
                return
            
            links_v  = self.calculate_voltage(self.meetpin_links_voor.value)
            rechts_v = self.calculate_voltage(self.meetpin_rechts_voor.value)

            links_op_lijn  = links_v  > 0.5
            rechts_op_lijn = rechts_v > 0.5

            if links_op_lijn and rechts_op_lijn:
                self.log("correct vooruit aan het rijden LDR achter:" + str(self.calculate_voltage(self.meetpin_achter.value)))
                self.right_power.value = True;  self.right_direction.value = False
                self.left_power.value  = True;  self.left_direction.value  = False
            elif not links_op_lijn and rechts_op_lijn:
                self.log("links niet op lijn")
                self.log("LDR links:" + str(self.calculate_voltage(self.meetpin_links_voor.value)))
                self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
                self.right_power.value = True;  self.right_direction.value = False
                self.left_power.value  = False; self.left_direction.value  = True
            elif links_op_lijn and not rechts_op_lijn:
                self.log("rechts niet op lijn")
                self.log("LDR links:" + str(self.calculate_voltage(self.meetpin_links_voor.value)))
                self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
                self.right_power.value = False; self.right_direction.value = False
                self.left_power.value  = True;  self.left_direction.value  = False
            else:
                self.right_power.value = True;  self.right_direction.value = False
                self.left_power.value  = True; self.left_direction.value  = True

            time.sleep(0.01)
        self.log("over kruispunt gekomen nog beetje vooruit aan het rijden")
        self.right_power.value = True;  self.right_direction.value = False
        self.left_power.value  = True;  self.left_direction.value  = False
        time.sleep(0.3)
        if extra_tijd:
            time.sleep(extra_tijd)
        self.huidige_tijd = time.monotonic()
        self.stop()
        '''

    def rijd_achteruit(self):
        self.log("achteruit aan het rijden")
        self.right_power.value = True;  self.right_direction.value = True
        self.left_power.value  = True;  self.left_direction.value  = True
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_achter.value) < 0.45:
            time.sleep(0.1)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def draai_links(self):
        self.log("Links aan het draaien")
        self.right_power.value = True;  self.right_direction.value = False
        self.left_power.value  = True;  self.left_direction.value  = True
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_links_voor.value) < 0.5:
            time.sleep(0.01)
        #while self.calculate_voltage(self.meetpin_links_voor.value) < 1:
            #time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met links draaien")
        self.log("LDR links:" + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()

    def draai_rechts(self):
        self.log("Rechts aan het draaien")
        self.right_power.value = True;  self.right_direction.value = False
        self.left_power.value  = True;  self.left_direction.value  = True
        time.sleep(0.3)
        #while self.calculate_voltage(self.meetpin_rechts_voor.value) > 0.95:
            #time.sleep(0.01)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) < 0.45:
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.log("klaar met rechts draaien")
        self.log("LDR links:" + str(self.calculate_voltage(self.meetpin_links_voor.value)))
        self.log("LDR rechts:" + str(self.calculate_voltage(self.meetpin_rechts_voor.value)))
        self.stop()
    
    def positioneer_toren(self):
        self.stop()
        time.sleep(0.2)
        self.rijd_achteruit()
        self.rijd_vooruit(0.2) #dit moet ge teste tot het juist is
        self.stop()
        self.stappenmotor.plaats_toren()
    
    def noodstop_gedetecteerd(self):
        # Pull.UP = knop ingedrukt is LOW
        if not self.noodstop_knop.value:
            self.noodstop_actief = True
            self.log("NOODSTOP ingedrukt!")
            self.stop()
            return True
        return False
        
        
