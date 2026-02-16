import board
import digitalio
import time
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

counter = 0

while counter<3:
    led1.value = True
    time.sleep(0.6)
    led2.value = True
    time.sleep(0.5)
    led3.value = True
    time.sleep(0.4)
    led4.value = True
    time.sleep(0.3)
    led5.value = True
    time.sleep(0.2)
    led6.value = True
    time.sleep(0.1)
    led7.value = True
    time.sleep(1)
    led1.value = False
    led2.value = False
    led3.value = False
    led4.value = False
    led5.value = False
    led6.value = False
    led7.value = False
    time.sleep(2)
    counter += 1
    print(counter)
