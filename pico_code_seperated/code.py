import socketpool
import wifi
import time
import json
from adafruit_httpserver import Server, Request, Response, GET, Websocket

from rijden      import Rijder
from stappenmotor import Stappenmotor
from pad         import Pad

websocket = None

def log(bericht):
    # Print naar console en stuur naar de verbonden websocket client.
    print(bericht)
    if websocket is not None:
        try:
            websocket.send_message("LOG: " + str(bericht))
        except Exception:
            pass

stappenmotor = Stappenmotor(log=log)
rijder       = Rijder(stappenmotor, log=log)
pad          = Pad(rijder, log=log)

# --- WiFi & server ---
SSID     = "PICO-TEAM-110"
PASSWORD = "wachtwoord110"

wifi.radio.start_ap(ssid=SSID, password=PASSWORD)
log("My IP address is" + str(wifi.radio.ipv4_address_ap))

pool      = socketpool.SocketPool(wifi.radio)
server    = Server(pool, "/static", debug=True)

@server.route("/connect-websocket", GET)
def connect_client(request: Request):
    global websocket
    if websocket is not None:
        websocket.close()
    websocket = Websocket(request)
    return websocket

server.start(str(wifi.radio.ipv4_address_ap), 80)

# --- Hoofdlus ---
while True:
    server.poll()

    if websocket is not None:
        data = websocket.receive(fail_silently=True)

        if data is not None:
            cmd = data.strip()
            log("RECEIVED:" + repr(cmd))

            if cmd.startswith("{"):
                try:
                    #berekend pad word doorgestuurd
                    payload = json.loads(cmd)
                    pad.laad_pad(payload["pad"], payload["groen"])
                    pad.voer_stap_uit()
                except Exception as e:
                    log("Fout bij parsen pad:" + str(e))

            #aparte commands worden doorgestuurd
            elif cmd == "waypoint":
                pad.voer_stap_uit()
            elif cmd == "move_forward":
                rijder.rijd_vooruit()
            elif cmd == "move_back":
                rijder.rijd_achteruit()
            elif cmd == "move_left":
                rijder.draai_links()
            elif cmd == "move_right":
                rijder.draai_rechts()
            elif cmd == "stop":
                rijder.websocket_stop = True
                rijder.stop()
                rijder.zet_led_rgb(0, 0, 0)
            elif cmd == "reset_noodstop":
                rijder.noodstop_actief = False
                log("Noodstop gereset.")

    time.sleep(0.01)
