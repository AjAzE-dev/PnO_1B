import board
import time
import digitalio
from analogio import AnalogIn

led1 = digitalio.DigitalInOut(board.GP22)
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.GP21)
led2.direction = digitalio.Direction.OUTPUT

led3 = digitalio.DigitalInOut(board.GP20)
led3.direction = digitalio.Direction.OUTPUT

led4 = digitalio.DigitalInOut(board.GP19)
led4.direction = digitalio.Direction.OUTPUT

led5 = digitalio.DigitalInOut(board.GP18)
led5.direction = digitalio.Direction.OUTPUT

led6 = digitalio.DigitalInOut(board.GP17)
led6.direction = digitalio.Direction.OUTPUT

led7 = digitalio.DigitalInOut(board.GP16)
led7.direction = digitalio.Direction.OUTPUT

def calculate_voltage(value):
    return (value * 3.3) / 65535


meetpin = AnalogIn(board.GP27)
while True:
    meting = meetpin.value
    print(meting)

    voltage = calculate_voltage(meting)
    print(voltage)


    if voltage < 0.41:
        led1.value = True
    else:
        led1.value = False

    if voltage < 0.82:
        led2.value = True
    else:
        led2.value = False

    if voltage < 1.23:
        led3.value = True
    else:
        led3.value = False

    if voltage < 1.64:
        led4.value = True
    else:
        led4.value = False

    if voltage < 2.05:
        led5.value = True
    else:
        led5.value = False

    if voltage < 2.46:
        led6.value = True
    else:
        led6.value = False

    if voltage < 2.87:
        led7.value = True
    else:
        led7.value = False

    time.sleep(0.5)
