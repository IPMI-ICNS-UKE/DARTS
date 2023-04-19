
class Dartboard:
    def __init__(self, n):
        self.numberOfFields = n

    def execute(self, channel, parameters):
        print(self.give_name())
        return self.apply_dartboard_on_membrane(channel, parameters)

    # returns areas that divide a circular ROI into n sub-ROIs
    def apply_dartboard_on_membrane(self, channel_membrane, parameters):
        dartboard_areas = []
        dartboard_areas.append(DartboardArea())
        return channel_membrane

    def give_name(self):
        return "dartboard erstellt"


class DartboardArea:
    def measure(self):
        return 0