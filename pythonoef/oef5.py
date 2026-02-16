import board
import digitalio
import time

led1 = digitalio.DigitalInOut(board.GP22)
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.GP21)
led2.direction = digitalio.Direction.OUTPUT

reftijd = time.monotonic()
reftijd2 = time.monotonic()
while True:
    nu = time.monotonic()
    if nu - reftijd >= 1.0:
        led1.value = not led1.value
        reftijd = nu
        print(nu)
    if nu - reftijd2 >= 0.3:
        led2.value = not led2.value
        reftijd2 = nu
        print(nu)
    time.sleep(0.01)
