
class BaseBleaching:
    def execute(self, input_roi, parameters):
        bleaching_corrected = self.bleaching_correction(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def bleaching_correction(self, input_roi, parameters):
        wavelength = input_roi.get_wavelength()

        # bleaching corrections in reference channel and sensor channel are different
        if wavelength == parameters["wavelength_1"]:
            pass
        elif wavelength == parameters["wavelength_2"]:
            pass
        return input_roi

    def give_name(self):
        return "bleaching corrected"


class BleachingExponentialFit (BaseBleaching):
    def __init__(self):
        pass