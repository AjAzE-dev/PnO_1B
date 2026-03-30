import digitalio
import board
import busio
import adafruit_us100
from analogio import AnalogIn
from adafruit_httpserver import Server, Request, Response, GET, Websocket
import time

OBSTAKEL_DREMPEL_CM = 20

class Rijder:
    def __init__(self):
        self.log = log or print
        
        # --- Motor pinnen ---
        self.right_power = digitalio.DigitalInOut(board.GP0)
        self.right_power.direction = digitalio.Direction.OUTPUT
        self.right_direction = digitalio.DigitalInOut(board.GP1)
        self.right_direction.direction = digitalio.Direction.OUTPUT
        self.left_power = digitalio.DigitalInOut(board.GP2)
        self.left_power.direction = digitalio.Direction.OUTPUT
        self.left_direction = digitalio.DigitalInOut(board.GP3)
        self.left_direction.direction = digitalio.Direction.OUTPUT

        # --- Lijnvolg sensoren ---
        self.meetpin_rechts_voor = AnalogIn(board.GP26)
        self.meetpin_links_voor  = AnalogIn(board.GP27)
        self.meetpin_achter      = AnalogIn(board.GP28)

        # --- Ultrasone sensor (US-100) ---
        uart = busio.UART(board.GP4, board.GP5, baudrate=9600)
        self.us100 = adafruit_us100.US100(uart)

        self.huidige_tijd = time.monotonic()

    def calculate_voltage(self, value):
        return (value * 3.3) / 65535

    def obstakel_gedetecteerd(self):
        try:
            afstand = self.us100.distance
            return afstand is not None and afstand < OBSTAKEL_DREMPEL_CM
        except Exception:
            return False

    def stop(self):
        self.right_power.value = False
        self.left_power.value  = False

    def rijd_vooruit(self):
        while self.calculate_voltage(self.meetpin_achter.value) > 0.9 or  (time.monotonic() - self.huidige_tijd) < 0.3:
            if self.obstakel_gedetecteerd():
                self.log("Obstakel gedetecteerd! Gestopt.")
                self.stop()
                return

            links_v  = self.calculate_voltage(self.meetpin_links_voor.value)
            rechts_v = self.calculate_voltage(self.meetpin_rechts_voor.value)

            links_op_lijn  = links_v  < 0.95
            rechts_op_lijn = rechts_v < 0.95

            if links_op_lijn and rechts_op_lijn:
                self.right_power.value = True;  self.right_direction.value = True
                self.left_power.value  = True;  self.left_direction.value  = True
            elif not links_op_lijn and rechts_op_lijn:
                self.right_power.value = True;  self.right_direction.value = True
                self.left_power.value  = False; self.left_direction.value  = True
            elif links_op_lijn and not rechts_op_lijn:
                self.right_power.value = False; self.right_direction.value = True
                self.left_power.value  = True;  self.left_direction.value  = True
            else:
                self.right_power.value = True;  self.right_direction.value = True
                self.left_power.value  = False; self.left_direction.value  = True

            time.sleep(0.01)

        self.right_power.value = True;  self.right_direction.value = True
        self.left_power.value  = True;  self.left_direction.value  = True
        time.sleep(0.3)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def rijd_achteruit(self):
        self.log("achteruit aan het rijden")
        self.right_power.value = True;  self.right_direction.value = False
        self.left_power.value  = True;  self.left_direction.value  = False
        time.sleep(0.5)
        while self.calculate_voltage(self.meetpin_achter.value) > 0.9:
            time.sleep(0.1)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def draai_links(self):
        self.right_power.value = True;  self.right_direction.value = False
        self.left_power.value  = True;  self.left_direction.value  = True
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_links_voor.value) > 0.95:
            time.sleep(0.01)
        while self.calculate_voltage(self.meetpin_links_voor.value) < 1:
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.stop()

    def draai_rechts(self):
        self.right_power.value = True;  self.right_direction.value = True
        self.left_power.value  = True;  self.left_direction.value  = False
        time.sleep(0.3)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) > 0.95:
            time.sleep(0.01)
        while self.calculate_voltage(self.meetpin_rechts_voor.value) < 1:
            time.sleep(0.01)
        self.huidige_tijd = time.monotonic()
        self.stop()
    
