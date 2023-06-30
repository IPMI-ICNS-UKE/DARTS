import pandas as pd
import skimage
from stardist.models import StarDist2D
from csbdeep.utils import normalize

import numpy as np

class BaseBleaching:
    def execute(self, input_roi, parameters):
        bleaching_corrected = self.bleaching_correction(input_roi, parameters)
        print(self.give_name())
        return bleaching_corrected

    def give_name(self):
        return "bleaching corrected"


class BleachingExponentialFit (BaseBleaching):
    pass

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

    def add_value_to_each_pixel_in_region(self, image, value):
        copy = image.copy()
        for y in range(len(copy)):
            for x in range(len(copy[0])):
                if copy[y][x] > 0.1:
                    copy[y][x] += value

        return copy

    def give_name(self):
        return "Bleaching correction (additive no fit)"
