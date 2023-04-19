
class BaseDecon:
    def execute(self, input_roi, parameters):
        processed_roi = self.deconvolve(input_roi, parameters)
        print(self.give_name())
        return processed_roi

    def give_name(self):
        return "...deconvolution.."

    def deconvolve(self, input_roi, parameters):
        return input_roi