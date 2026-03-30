import socketpool
import wifi
import time
import json
import digitalio
import board
import busio
import adafruit_us100
from analogio import AnalogIn
from adafruit_httpserver import Server, Request, Response, GET, Websocket

# --- Motor pinnen ---
right_power = digitalio.DigitalInOut(board.GP0)
right_power.direction = digitalio.Direction.OUTPUT
right_direction = digitalio.DigitalInOut(board.GP1)
right_direction.direction = digitalio.Direction.OUTPUT
left_power = digitalio.DigitalInOut(board.GP2)
left_power.direction = digitalio.Direction.OUTPUT
left_direction = digitalio.DigitalInOut(board.GP3)
left_direction.direction = digitalio.Direction.OUTPUT

# --- Lijnvolg sensoren ---
meetpin_rechts_voor = AnalogIn(board.GP26)
meetpin_links_voor  = AnalogIn(board.GP27)
meetpin_achter      = AnalogIn(board.GP28)

# --- Ultrasone sensor (US-100) ---
uart  = busio.UART(board.GP4, board.GP5, baudrate=9600)
us100 = adafruit_us100.US100(uart)

OBSTAKEL_DREMPEL_CM = 20

# --- Stappenmotoren ---
IN1 = digitalio.DigitalInOut(board.GP18)
IN2 = digitalio.DigitalInOut(board.GP19)
IN3 = digitalio.DigitalInOut(board.GP20)
IN4 = digitalio.DigitalInOut(board.GP21)
IN5 = digitalio.DigitalInOut(board.GP13)
IN6 = digitalio.DigitalInOut(board.GP12)
IN7 = digitalio.DigitalInOut(board.GP11)
IN8 = digitalio.DigitalInOut(board.GP10)

for pin in (IN1, IN2, IN3, IN4, IN5, IN6, IN7, IN8):
    pin.direction = digitalio.Direction.OUTPUT
    pin.value = False

step_delay = 0.001

def Step1():
    IN4.value = True;  IN8.value = True;  IN5.value = True
    time.sleep(step_delay)
    IN4.value = False; IN8.value = False; IN5.value = False

def Step2():
    IN4.value = True;  IN3.value = True;  IN5.value = True
    time.sleep(step_delay)
    IN4.value = False; IN3.value = False; IN5.value = False

def Step3():
    IN3.value = True;  IN5.value = True;  IN6.value = True
    time.sleep(step_delay)
    IN3.value = False; IN5.value = False; IN6.value = False

def Step4():
    IN2.value = True;  IN3.value = True;  IN6.value = True
    time.sleep(step_delay)
    IN2.value = False; IN3.value = False; IN6.value = False

def Step5():
    IN2.value = True;  IN6.value = True;  IN7.value = True
    time.sleep(step_delay)
    IN2.value = False; IN6.value = False; IN7.value = False

def Step6():
    IN1.value = True;  IN2.value = True;  IN7.value = True
    time.sleep(step_delay)
    IN1.value = False; IN2.value = False; IN7.value = False

def Step7():
    IN1.value = True;  IN7.value = True;  IN8.value = True
    time.sleep(step_delay)
    IN1.value = False; IN7.value = False; IN8.value = False

def Step8():
    IN4.value = True;  IN1.value = True;  IN8.value = True
    time.sleep(step_delay)
    IN4.value = False; IN1.value = False; IN8.value = False

def stappenmotor_links(stappen):
    for i in range(stappen):
        Step1(); Step2(); Step3(); Step4()
        Step5(); Step6(); Step7(); Step8()

def stappenmotor_rechts(stappen):
    for i in range(stappen):
        Step8(); Step7(); Step6(); Step5()
        Step4(); Step3(); Step2(); Step1()

def plaats_toren():
    print("Toren plaatsen...")
    stappenmotor_links(127)  # beide motoren 90° draaien
    print("Toren geplaatst.")


# --- Rijfuncties ---
def calculate_voltage(value):
    return (value * 3.3) / 65535

def obstakel_gedetecteerd():
    try:
        afstand = us100.distance
        return afstand is not None and afstand < OBSTAKEL_DREMPEL_CM
    except Exception:
        return False

def stop():
    right_power.value = False
    left_power.value  = False

def rijd_vooruit():
    while calculate_voltage(meetpin_achter.value) > 0.9:
        if obstakel_gedetecteerd():
            print("Obstakel gedetecteerd! Gestopt.")
            stop()
            return

        links_v  = calculate_voltage(meetpin_links_voor.value)
        rechts_v = calculate_voltage(meetpin_rechts_voor.value)

        links_op_lijn  = links_v  < 0.8
        rechts_op_lijn = rechts_v < 0.8

        if links_op_lijn and rechts_op_lijn:
            right_power.value = True;  right_direction.value = True
            left_power.value  = True;  left_direction.value  = True
        elif not links_op_lijn and rechts_op_lijn:
            right_power.value = True;  right_direction.value = True
            left_power.value  = False; left_direction.value  = True
        elif links_op_lijn and not rechts_op_lijn:
            right_power.value = False; right_direction.value = True
            left_power.value  = True;  left_direction.value  = True
        else:
            right_power.value = True;  right_direction.value = True
            left_power.value  = False; left_direction.value  = True

        time.sleep(0.01)

    right_power.value = True;  right_direction.value = True
    left_power.value  = True;  left_direction.value  = True
    time.sleep(0.3)
    stop()

def rijd_achteruit():
    print("achteruit aan het rijden")
    right_power.value = True;  right_direction.value = False
    left_power.value  = True;  left_direction.value  = False
    time.sleep(0.5)
    while calculate_voltage(meetpin_achter.value) > 0.8:
        time.sleep(0.1)
    stop()

def draai_links():
    right_power.value = True;  right_direction.value = False
    left_power.value  = True;  left_direction.value  = True
    time.sleep(0.3)
    while calculate_voltage(meetpin_links_voor.value) > 0.8:
        time.sleep(0.01)
    while calculate_voltage(meetpin_links_voor.value) < 1:
        time.sleep(0.01)
    stop()

def draai_rechts():
    right_power.value = True;  right_direction.value = True
    left_power.value  = True;  left_direction.value  = False
    time.sleep(0.3)
    while calculate_voltage(meetpin_rechts_voor.value) > 0.8:
        time.sleep(0.01)
    while calculate_voltage(meetpin_rechts_voor.value) < 1:
        time.sleep(0.01)
    stop()


# --- Padberekening ---
instructies  = []
groen_coords = []
pad_index    = 0

def bereken_richting(van, naar):
    dy = naar[0] - van[0]
    dx = naar[1] - van[1]
    if dy == 1:  return "achter"
    if dy == -1: return "voor"
    if dx == 1:  return "rechts"
    if dx == -1: return "links"
    return None

def bereken_bochten(pad):
    resultaat    = []
    kijkrichting = "voor"
    volgorde     = ["voor", "rechts", "achter", "links"]

    for i in range(len(pad) - 1):
        beweeg = bereken_richting(pad[i], pad[i + 1])
        if beweeg is None:
            continue
        if beweeg == kijkrichting:
            resultaat.append(("voor", pad[i + 1]))
        else:
            huidig_idx = volgorde.index(kijkrichting)
            doel_idx   = volgorde.index(beweeg)
            stappen    = (doel_idx - huidig_idx) % 4

            if stappen == 1:
                resultaat.append(("draai_rechts", pad[i + 1]))
            elif stappen == 3:
                resultaat.append(("draai_links", pad[i + 1]))
            elif stappen == 2:
                resultaat.append(("achter", pad[i + 1]))

            kijkrichting = beweeg

    return resultaat

def is_groene_stop(coord):
    # coord is [r, c], groen_coords is lijst van [r, c]
    for g in groen_coords:
        if g[0] == coord[0] and g[1] == coord[1]:
            return True
    return False

def voer_stap_uit():
    global pad_index
    if pad_index < len(instructies):
        if obstakel_gedetecteerd():
            print("Obstakel gedetecteerd! Pad onderbroken.")
            stop()
            return

        stap, coord = instructies[pad_index]
        pad_index += 1
        print("Uitvoeren:", stap, "naar", coord)

        if stap == "voor":
            rijd_vooruit()
        elif stap == "draai_links":
            draai_links()
            rijd_vooruit()
        elif stap == "draai_rechts":
            draai_rechts()
            rijd_vooruit()

        # Controleer na elke stap of toren geplaatst moet worden
        if is_groene_stop(coord):
            plaats_toren()

        voer_stap_uit()
    else:
        print("Pad voltooid.")
        stop()


# --- WiFi & server ---
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

            if cmd.startswith("{"):
                try:
                    payload      = json.loads(cmd)
                    pad_coords   = payload["pad"]
                    groen_coords = payload["groen"]
                    instructies  = bereken_bochten(pad_coords)
                    pad_index    = 0
                    print("Pad ontvangen:", pad_coords)
                    print("Groene stops:", groen_coords)
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

    time.sleep(0.01)