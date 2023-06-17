import pandas as pd
import skimage
from stardist.models import StarDist2D
from csbdeep.utils import normalize

class BaseBleaching:
    def execute(self, input_roi, parameters):
        bleaching_corrected = self.bleaching_correction(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def give_name(self):
        return "bleaching corrected"


class BleachingExponentialFit (BaseBleaching):
    pass

class BleachingAdditiveFit (BaseBleaching):

    def run(self, cell, parameters, model):
        bleaching_channel_copy = cell.give_image_channel2()
        area_list = cell.return_list_of_areas()
        mean_intensity_frame_zero = cell.calculate_mean_value_in_channel_frame(0,2)

        for frame_index in range(len(bleaching_channel_copy)):
            current_area = area_list[frame_index]
            current_mean_intensity = cell.calculate_mean_value_in_channel_frame(frame_index,2)
            value_to_add = self.calculate_value_to_add(mean_intensity_frame_zero,current_mean_intensity,current_area)

            bleaching_channel_copy[frame_index] = self.add_value_to_each_pixel_in_region(
                bleaching_channel_copy[frame_index], value_to_add)

        cell.set_image_channel2(bleaching_channel_copy)



    def calculate_value_to_add(self, mean_intensity_reference, mean_intensity_bleached, number_of_pixels):
        mean_intensity_difference = mean_intensity_reference - mean_intensity_bleached
        value_to_add_to_each_pixel = float(mean_intensity_difference) / number_of_pixels
        # print("value to add")
        # print(str(value_to_add_to_each_pixel))
        return value_to_add_to_each_pixel

    def add_value_to_each_pixel_in_region(self, image, value):
        copy = image.copy()
        for y in range(len(copy)):
            for x in range(len(copy[0])):
                if copy[y][x] > 0.1:
                    copy[y][x] += value

        return copy
