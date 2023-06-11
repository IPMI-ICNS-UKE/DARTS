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
    def __init__(self):
        self.model = StarDist2D.from_pretrained('2D_versatile_fluo')

    def run(self, cell, parameters):
        bleaching_channel_copy = cell.give_image_channel2()
        bleaching_image_series_data = self.get_mean_value_and_area_list(bleaching_channel_copy)
        area_list = self.get_area_list(bleaching_image_series_data)
        mean_intensity_list = self.get_mean_intensity_list(bleaching_image_series_data)
        mean_intensity_frame_zero = mean_intensity_list[0]

        frame_index = 0
        for frame in bleaching_channel_copy:
            current_area = area_list[frame_index]
            current_mean_intensity = mean_intensity_list[frame_index]
            value_to_add = self.calculate_value_to_add(mean_intensity_frame_zero,current_mean_intensity,current_area)
            bleaching_channel_copy[frame_index] = self.add_value_to_each_pixel_in_region(
                bleaching_channel_copy[frame_index], value_to_add)
            frame_index += 1

        cell.set_image_channel2(bleaching_channel_copy)

    def get_mean_value_and_area_list(self, bleaching_image_series):
        labels_for_each_frame = []

        for frame in range(len(bleaching_image_series)):
            img_label, img_detail = self.model.predict_instances(normalize(bleaching_image_series[frame]))
            labels_for_each_frame.append(img_label)

        features = pd.DataFrame()
        for num, img in enumerate(bleaching_image_series):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                features = features._append([{'area': region.area,
                                              'mean_intensity': region.intensity_mean
                                              }, ])

        return features

    def get_area_list(self, dataframe):
        area_list = dataframe["area"].values.tolist()
        return area_list

    def get_mean_intensity_list(self,dataframe):
        area_list = dataframe["mean_intensity"].values.tolist()
        return area_list



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
                if copy[y][x] > 0:
                    copy[y][x] += round(value)

        return copy