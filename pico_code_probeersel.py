import socketpool
import wifi
import time
import json
import digitalio
import board
from analogio import AnalogIn
from adafruit_httpserver import Server, Request, Response, GET, Websocket


right_power = digitalio.DigitalInOut(board.GP0)
right_power.direction = digitalio.Direction.OUTPUT
right_direction = digitalio.DigitalInOut(board.GP1)
right_direction.direction = digitalio.Direction.OUTPUT
left_power = digitalio.DigitalInOut(board.GP2)
left_power.direction = digitalio.Direction.OUTPUT
left_direction = digitalio.DigitalInOut(board.GP3)
left_direction.direction = digitalio.Direction.OUTPUT

meetpin_rechts_voor = AnalogIn(board.GP26)
meetpin_links_voor = AnalogIn(board.GP27)
meetpin_achter = AnalogIn(board.GP28)

def calculate_voltage(value):
    return (value * 3.3) / 65535

def stop():
    right_power.value = False
    left_power.value = False

def rijd_vooruit():
    right_power.value = True
    right_direction.value = True
    left_power.value = True
    left_direction.value = True

def rijd_achteruit():
    right_power.value = True
    right_direction.value = False
    left_power.value = True
    left_direction.value = False

def draai_links():
    right_power.value = True
    right_direction.value = True
    left_power.value = True
    left_direction.value = False
    while (calculate_voltage(meetpin_links_voor.value) > 0.9 and calculate_voltage(meetpin_rechts_voor.value) > 0.7):
        time.sleep(0.01)
    stop()

def draai_rechts():
    right_power.value = True
    right_direction.value = False
    left_power.value = True
    left_direction.value = True
    while (calculate_voltage(meetpin_links_voor.value) > 0.9 and calculate_voltage(meetpin_rechts_voor.value) > 0.7):
        time.sleep(0.01)
    stop()

instructies = []
pad_index   = 0

def bereken_richting(van, naar):
    dy = naar[0] - van[0]
    dx = naar[1] - van[1]
    if dy == 1:  return "voor"
    if dy == -1: return "achter"
    if dx == 1:  return "rechts"
    if dx == -1: return "links"
    return None

def bereken_bochten(pad):
    resultaat = []
    kijkrichting = "voor"
    volgorde = ["voor", "rechts", "achter", "links"]

    for i in range(len(pad) - 1):
        beweeg = bereken_richting(pad[i], pad[i + 1])
        if beweeg == kijkrichting:
            resultaat.append("voor")
        else:
            huidig_idx = volgorde.index(kijkrichting)
            doel_idx   = volgorde.index(beweeg)
            stappen    = (doel_idx - huidig_idx) % 4

            if stappen == 1:
                resultaat.append("draai_rechts")
            elif stappen == 3:
                resultaat.append("draai_links")
            elif stappen == 2:
                resultaat.append("draai_links")
                resultaat.append("draai_links")

            resultaat.append("voor")
            kijkrichting = beweeg

    return resultaat

def voer_stap_uit():
    global pad_index
    if pad_index < len(instructies):
        stap = instructies[pad_index]
        pad_index += 1
        print("Uitvoeren:", stap)
        if stap == "voor":
            rijd_vooruit()
        elif stap == "draai_links":
            draai_links()
            rijd_vooruit()
        elif stap == "draai_rechts":
            draai_rechts()
            rijd_vooruit()
    else:
        print("Pad voltooid.")
        stop()

SSID     = "PICO-TEAM-110"
PASSWORD = "wachtwoord110"

wifi.radio.start_ap(ssid=SSID, password=PASSWORD)
print("My IP address is", wifi.radio.ipv4_address_ap)

pool      = socketpool.SocketPool(wifi.radio)
server    = Server(pool, "/static", debug=True)
websocket = None

@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket
    if websocket is not None:
        websocket.close()
    websocket = Websocket(request)
    return websocket

server.start(str(wifi.radio.ipv4_address_ap), 80)

while True:
    server.poll()

    if websocket is not None:
        data = websocket.receive(fail_silently=True)
        if data is not None:
            cmd = data.strip()
            print("RECEIVED:", repr(cmd))

            if cmd.startswith("[["):
                try:
                    pad_coords = json.loads(cmd)
                    instructies = bereken_bochten(pad_coords)
                    pad_index   = 0
                    print("Pad ontvangen:", pad_coords)
                    print("Instructies:", instructies)
                    voer_stap_uit() 
                except Exception as e:
                    print("Fout bij parsen pad:", e)

            elif cmd == "waypoint":
                voer_stap_uit()

            elif cmd == "move_forward":
                rijd_vooruit()
            elif cmd == "move_back":
                rijd_achteruit()
            elif cmd == "move_left":
                draai_links()
            elif cmd == "move_right":
                draai_rechts()
            elif cmd == "stop":
                stop()

        
        if meetpin_achter < 0.9:
            voer_stap_uit()
            time.sleep(0.5)  # zodat 1 waypoint niet meerdere keren triggert

    time.sleep(0.01)