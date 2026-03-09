import socketpool
import wifi
import time
import digitalio
import board
from adafruit_httpserver import Server, Request, Response, GET, Websocket


SSID = "PICO-TEAM-110"  #Verander X naar groepsnummer
PASSWORD = "wachtwoord110"  #Verander voor veiligheidsredenen

pin0 = digitalio.DigitalInOut(board.GP0) 
pin0.direction = digitalio.Direction.OUTPUT

pin1 = digitalio.DigitalInOut(board.GP1) 
pin1.direction = digitalio.Direction.OUTPUT

black_line = 0

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
            
            if 

            if data.strip() == "move_forward":
                print("TURNING MOTOR ON")
                pin0.value = True
                pin1.value = False
            if data.strip() == "move_left":
                print("TURNING MOTOR OFF")
                pin0.value = False
                pin1.value = False
            if data.strip() == "move_down":
                print("TURNING MOTOR OFF")
                pin0.value = True
                pin1.value = True

    time.sleep(0.1)
