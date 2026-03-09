#Library Import
import digitalio
import board
import time
from analogio import AnalogIn

#functie om Spanning te meten
def calculate_voltage(value):
    return (value * 3.3) / 65535

#meetpinnen
meetpin_rechts_voor = AnalogIn(board.GP26)
meetpin_links_voor = AnalogIn(board.GP27)
meetpin_achter = AnalogIn(board.GP28)


for i in range(1000):

    measurement_links_voor = meetpin_links_voor.value
    measurement_rechts_voor = meetpin_rechts_voor.value
    measurement_achter = meetpin_achter.value



    voltage_links_voor = calculate_voltage(measurement_links_voor)
    voltage_rechts_voor = calculate_voltage(measurement_rechts_voor)
    voltage_achter = calculate_voltage(measurement_achter)

    verschil_linksvoor_en_rechtsvoor = voltage_links_voor - voltage_rechts_voor
    gemiddelde_linksvoor_en_rechtsvoor = (voltage_rechts_voor + voltage_links_voor)/2

    tuple_waarde = (
        i+1,
        voltage_links_voor,
        voltage_rechts_voor,
        voltage_achter,
        verschil_linksvoor_en_rechtsvoor,
        gemiddelde_linksvoor_en_rechtsvoor)

    print(tuple_waarde)
    time.sleep(0.1)

