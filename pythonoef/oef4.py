import board
import pwmio
import time
from analogio import AnalogIn

meetpin = AnalogIn(board.GP27)
output_pwm1 = pwmio.PWMOut(board.GP22,frequency=1000)

while True:
    meting = meetpin.value
    output_pwm1.duty_cycle  = 65535 - meting
