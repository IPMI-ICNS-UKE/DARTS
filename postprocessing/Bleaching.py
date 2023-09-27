
import numpy as np
from scipy.optimize import curve_fit

class BaseBleaching:
    def execute(self, input_roi, parameters):
        bleaching_corrected = self.bleaching_correction(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def give_name(self):
        return "bleaching corrected"

    def add_value_to_each_pixel_in_region(self, image, value):
        copy = image.copy()
        for y in range(len(copy)):
            for x in range(len(copy[0])):
                if copy[y][x] > 0.05:
                    copy[y][x] += value

        return copy
#

def biexponential_decay(x, A1, A2, tau1, tau2):
    return A1 * np.exp(-x / tau1) + A2 * np.exp(-x / tau2)

class BleachingBiexponentialFitAdditive (BaseBleaching):

    def run(self, cell, parameters, model):
        bleaching_channel_copy = cell.give_image_channel2()
        frame_number = len(bleaching_channel_copy)
        x_values = np.arange(frame_number)
        y_values = np.asarray([cell.calculate_mean_value_in_channel_frame(frame_index, 2) for frame_index in range(frame_number)])
        initial_guess = [1800, 1, 2000, 1]
        popt, pcov = curve_fit(f=biexponential_decay, xdata=x_values, ydata=y_values, p0=initial_guess)
        x, A1, A2, tau1, tau2 = popt
        mean_intensity_first_frame_fitted = biexponential_decay(0, A1, A2, tau1, tau2)

        for frame in range(frame_number):
            fitted_mean_intensity_this_frame = biexponential_decay(x, A1, A2, tau1, tau2)
            differenz = mean_intensity_first_frame_fitted - fitted_mean_intensity_this_frame
            bleaching_channel_copy[frame] = self.add_value_to_each_pixel_in_region(bleaching_channel_copy[frame], differenz)

        cell.set_image_channel2(bleaching_channel_copy)


class BleachingAdditiveNoFit(BaseBleaching):

    def run(self, cell, parameters, model):
        bleaching_channel_copy = cell.give_image_channel2()
        mean_intensity_frame_zero = cell.calculate_mean_value_in_channel_frame(0, 2)

        for frame_index in range(len(bleaching_channel_copy)):
            current_mean_intensity = cell.calculate_mean_value_in_channel_frame(frame_index, 2)
            value_to_add = (mean_intensity_frame_zero - current_mean_intensity)
            bleaching_channel_copy[frame_index] = self.add_value_to_each_pixel_in_region(
                bleaching_channel_copy[frame_index], value_to_add)
        cell.set_image_channel2(bleaching_channel_copy)



    def give_name(self):
        return "Bleaching correction (additive no fit)"

class BleachingMultiplicativeSimple (BaseBleaching):
    def run(self, cell, parameters, model):
        bleaching_channel_copy = cell.give_image_channel2()
        mean_intensity_frame_zero = cell.calculate_mean_value_in_channel_frame(0, 2)

        for frame_index in range(len(bleaching_channel_copy)):
            current_mean_intensity = cell.calculate_mean_value_in_channel_frame(frame_index, 2)
            correction_factor = mean_intensity_frame_zero / current_mean_intensity

            bleaching_channel_copy[frame_index] = self.multiply_pixels_by_value(bleaching_channel_copy[frame_index], correction_factor)

        cell.set_image_channel2(bleaching_channel_copy)

    def multiply_pixels_by_value(self, image, factor):
        copy = image.copy()
        for y in range(len(copy)):
            for x in range(len(copy[0])):
                if copy[y][x] > 0.05:  # to prevent increase of background intensity
                    old_value = copy[y][x]
                    new_value = old_value * factor
                    if new_value < old_value:  # if overflow happened
                        new_value = np.iinfo(image.dtype).max  # set pixel to maximum possible value
                    copy[y][x] = new_value
        return copy