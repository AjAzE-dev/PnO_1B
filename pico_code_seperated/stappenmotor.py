import digitalio
import board
import time

step_delay = 0.001

class Stappenmotor:
    def __init__(self):
        self.IN1 = digitalio.DigitalInOut(board.GP18)
        self.IN2 = digitalio.DigitalInOut(board.GP19)
        self.IN3 = digitalio.DigitalInOut(board.GP20)
        self.IN4 = digitalio.DigitalInOut(board.GP21)
        self.IN5 = digitalio.DigitalInOut(board.GP13)
        self.IN6 = digitalio.DigitalInOut(board.GP12)
        self.IN7 = digitalio.DigitalInOut(board.GP11)
        self.IN8 = digitalio.DigitalInOut(board.GP10)

        for pin in (self.IN1, self.IN2, self.IN3, self.IN4,
                    self.IN5, self.IN6, self.IN7, self.IN8):
            pin.direction = digitalio.Direction.OUTPUT
            pin.value = False

    def _step(self, pins_on):
        for pin in (self.IN1, self.IN2, self.IN3, self.IN4,
                    self.IN5, self.IN6, self.IN7, self.IN8):
            pin.value = False
        for pin in pins_on:
            pin.value = True
        time.sleep(step_delay)
        for pin in pins_on:
            pin.value = False

    def Step1(self): self._step([self.IN4, self.IN8, self.IN5])
    def Step2(self): self._step([self.IN4, self.IN3, self.IN5])
    def Step3(self): self._step([self.IN3, self.IN5, self.IN6])
    def Step4(self): self._step([self.IN2, self.IN3, self.IN6])
    def Step5(self): self._step([self.IN2, self.IN6, self.IN7])
    def Step6(self): self._step([self.IN1, self.IN2, self.IN7])
    def Step7(self): self._step([self.IN1, self.IN7, self.IN8])
    def Step8(self): self._step([self.IN4, self.IN1, self.IN8])

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
        self.draai_links(127)
        self.log("Toren geplaatst.")
