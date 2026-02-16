import board
import digitalio
import time
led1 = digitalio.DigitalInOut(board.GP17)
led1.direction = digitalio.Direction.OUTPUT

counter = 0

while counter<3:
    led1.value = True
    time.sleep(2)
    led1.value = False
    time.sleep(1)
    counter += 1
    print(counter)

print("Xander")
