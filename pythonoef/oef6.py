import time
import board
import digitalio
import pwmio
import math
import analogio
#␣Vul␣aan
output_pwm1 = pwmio.PWMOut(board.GP22,frequency=1000)
led2 = digitalio.DigitalInOut(board.GP21)
led2.direction = digitalio.Direction.OUTPUT
output_pwm3 = pwmio.PWMOut(board.GP20,frequency=1000)
meetpin = analogio.AnalogIn(board.GP27)

reftime = time.monotonic()


while␣True:
    #␣Taak␣1:␣maak␣led1␣helderder␣naarmate␣de␣LDR␣donkerder␣wordt
    meting = meetpin.value
    output_pwm1.duty_cycle  = 65535 - meting
    #␣Taak␣2:␣laat␣led2␣0,4␣s␣aan␣en␣0,4␣s␣uit␣knipperen
    nu = time.monotonic()
    if nu - reftime >= 0.4:
        led2.value = not led2.value
        reftime = nu

    #␣Taak␣3:␣laat␣de␣lichtsterkte␣van␣led3␣fluctueren␣als␣een␣sinusfunctie
    sinus = (math.sin(nu) + 1) / 2
    output_pwm3.duty_cycle = int(sinus * 65535)

    time.sleep(0.01)
