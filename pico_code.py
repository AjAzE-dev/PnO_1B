import socketpool
import wifi
import time
import digitalio
import board
from adafruit_httpserver import Server, Request, Response, GET, Websocket


SSID = "PICO-TEAM-110"  #Verander X naar groepsnummer
PASSWORD = "wachtwoord110"  #Verander voor veiligheidsredenen

right_power = digitalio.DigitalInOut(board.GP0) 
right_power.direction = digitalio.Direction.OUTPUT

right_direction = digitalio.DigitalInOut(board.GP1) 
right_direction.direction = digitalio.Direction.OUTPUT

left_power = digitalio.DigitalInOut(board.GP1) 
left_power.direction = digitalio.Direction.OUTPUT

left_direction = digitalio.DigitalInOut(board.GP1) 
left_direction.direction = digitalio.Direction.OUTPUT

wifi.radio.start_ap(ssid=SSID, password=PASSWORD)

# print IP adres
print("My IP address is", wifi.radio.ipv4_address_ap)

pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)
websocket = None

# Deze functie wordt uitgevoerd wanneer de server een HTTP request ontvangt
@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket  # pylint: disable=global-statement

    if websocket is not None:
        websocket.close()  # Close any existing connection

    websocket = Websocket(request)

    return websocket


server.start(str(wifi.radio.ipv4_address_ap),80)

while True:
    server.poll()

    if websocket is not None:
        data = websocket.receive(fail_silently=True)
        if data is not None:
            print("RECEIVED:", repr(data))

            if data.strip() == "move_forward":
                print("TURNING MOTOR ON")
                right_power.value = True
                right_direction.value = True
            if data.strip() == "move_left":
                right_power.value = True
                left_power.value = True
                right_direction.value = True
                left_direction.value = False
            if data.strip() == "move_down":
                right_direction.value = True
                right_direction.value = False
            if data.strip() == "move_right":
                right_power.value = True
                left_power.value = True
                right_direction.value = False
                left_direction.value = True
            if data.strip() == "stop":
               right_power.value = False
               left_power.value = False 

    time.sleep(0.1)
