import digitalio
import board
import time

step_delay = 0.001

class Stappenmotor:
    def __init__(self, log=None):
        self.log = log or print
        self.IN1 = digitalio.DigitalInOut(board.GP9)
        self.IN2 = digitalio.DigitalInOut(board.GP8)
        self.IN3 = digitalio.DigitalInOut(board.GP7)
        self.IN4 = digitalio.DigitalInOut(board.GP6)
        self.IN5 = digitalio.DigitalInOut(board.GP13)
        self.IN6 = digitalio.DigitalInOut(board.GP12)
        self.IN7 = digitalio.DigitalInOut(board.GP11)
        self.IN8 = digitalio.DigitalInOut(board.GP10)

        for pin in (self.IN1, self.IN2, self.IN3, self.IN4,
                    self.IN5, self.IN6, self.IN7, self.IN8):
            pin.direction = digitalio.Direction.OUTPUT
            pin.value = False

    def Step1(self):
        self.IN4.value = True;  self.IN8.value = True;  self.IN5.value = True
        time.sleep(step_delay)
        self.IN4.value = False; self.IN8.value = False; self.IN5.value = False

    def Step2(self):
        self.IN4.value = True;  self.IN3.value = True;  self.IN5.value = True
        time.sleep(step_delay)
        self.IN4.value = False; self.IN3.value = False; self.IN5.value = False

    def Step3(self):
        self.IN3.value = True;  self.IN5.value = True;  self.IN6.value = True
        time.sleep(step_delay)
        self.IN3.value = False; self.IN5.value = False; self.IN6.value = False

    def Step4(self):
        self.IN2.value = True;  self.IN3.value = True;  self.IN6.value = True
        time.sleep(step_delay)
        self.IN2.value = False; self.IN3.value = False; self.IN6.value = False

    def Step5(self):
        self.IN2.value = True;  self.IN6.value = True;  self.IN7.value = True
        time.sleep(step_delay)
        self.IN2.value = False; self.IN6.value = False; self.IN7.value = False

    def Step6(self):
        self.IN1.value = True;  self.IN2.value = True;  self.IN7.value = True
        time.sleep(step_delay)
        self.IN1.value = False; self.IN2.value = False; self.IN7.value = False

    def Step7(self):
        self.IN1.value = True;  self.IN7.value = True;  self.IN8.value = True
        time.sleep(step_delay)
        self.IN1.value = False; self.IN7.value = False; self.IN8.value = False

    def Step8(self):
        self.IN4.value = True;  self.IN1.value = True;  self.IN8.value = True
        time.sleep(step_delay)
        self.IN4.value = False; self.IN1.value = False; self.IN8.value = False

    def draai_links(self, stappen):
        for _ in range(stappen):
            self.Step1(); self.Step2(); self.Step3(); self.Step4()
            self.Step5(); self.Step6(); self.Step7(); self.Step8()

    def draai_rechts(self, stappen):
        for _ in range(stappen):
            self.Step8(); self.Step7(); self.Step6(); self.Step5()
            self.Step4(); self.Step3(); self.Step2(); self.Step1()

    def plaats_toren(self):
        self.log("Toren plaatsen...")
        self.draai_rechts(127)
        self.log("Toren geplaatst.")