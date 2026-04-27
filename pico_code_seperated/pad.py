class Pad:
    def __init__(self, rijder, stappenmotor, log=None):
        self.rijder = rijder
        self.log = log or print
        self.instructies  = []
        self.groen_coords = []
        self.pad_index    = 0

    def laad_pad(self, pad_coords, groen_coords):
        self.groen_coords = groen_coords
        self.instructies  = self._bereken_bochten(pad_coords)
        self.pad_index    = 0
        self.log("Pad ontvangen: " + str(pad_coords))
        self.log("Groene stops: " + str(groen_coords))
        self.log("Instructies: " + str(self.instructies))

    def _bereken_richting(self, van, naar):
        dy = naar[0] - van[0]
        dx = naar[1] - van[1]
        if dy == 1:  return "achter"
        if dy == -1: return "voor"
        if dx == 1:  return "rechts"
        if dx == -1: return "links"
        return None

    def _bereken_bochten(self, pad):
        resultaat    = []
        kijkrichting = "voor"
        volgorde     = ["voor", "rechts", "achter", "links"]

        for i in range(len(pad) - 1):
            beweeg = self._bereken_richting(pad[i], pad[i + 1])
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

    def _is_groene_stop(self, coord):
        for g in self.groen_coords:
            if g[0] == coord[0] and g[1] == coord[1]:
                return True
        return False

    def voer_stap_uit(self):
        while self.pad_index < len(self.instructies):
            '''
            if self.rijder.noodstop_actief:
                self.log("Noodstop actief, pad gestopt.")
                return

            if self.rijder.obstakel_gedetecteerd():
                self.log("Obstakel gedetecteerd! Pad onderbroken.")
                self.rijder.stop()
                return
            '''

            stap, coord = self.instructies[self.pad_index]
            self.pad_index += 1
            self.log("Uitvoeren: " + str(stap) + " naar " + str(coord))

            groene_stop = self._is_groene_stop(coord)

            if stap == "voor":
                self.rijder.rijd_vooruit()
                if groene_stop:
                    self.rijder.positioneer_toren()

            elif stap == "draai_links":
                self.rijder.draai_links()
                if groene_stop:
                    self.rijder.positioneer_toren()
                self.rijder.rijd_vooruit()

            elif stap == "draai_rechts":
                self.rijder.draai_rechts()
                if groene_stop:
                    self.rijder.positioneer_toren()
                self.rijder.rijd_vooruit()

            elif stap == "achter":
                self.rijder.draai_links()
                self.rijder.draai_links()
                self.rijder.rijd_vooruit()
                if groene_stop:
                    self.rijder.positioneer_toren()

        self.log("Pad voltooid.")
        self.rijder.stop()