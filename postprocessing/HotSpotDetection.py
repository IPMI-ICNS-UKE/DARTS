
import pandas as pd
import trackpy as tp
import skimage
from tqdm import tqdm
import skimage.io as io
import numpy as np


class HotSpotDetector():
    def __init__(self, save_path, filename, fps):
        self.save_path = save_path
        self.filename = filename
        self.frames_per_second = fps

    def threshold_image_frame(self, threshold, image_series, frame):
        thresholded_frame = image_series[frame] > threshold
        return thresholded_frame

    def threshold_image_series(self, threshold, image_series):
        thresholded_image = image_series.copy()
        frame_number = len(image_series)
        for frame in range(frame_number):
            thresholded_image[frame] = self.threshold_image_frame(threshold, image_series, frame)
        return thresholded_image

    def label_thresholded_image_frame(self, thresholded_image):
        converted_thresholded_image = thresholded_image.astype(np.uint8)
        labeled_frame = skimage.measure.label(converted_thresholded_image, connectivity=2)
        return labeled_frame

    def label_thresholded_image_series(self, thresholded_image_series):
        frame_number = len(thresholded_image_series)
        labeled_image_series_list = []
        for frame in range(frame_number):
            labeled_image_series_list.append(self.label_thresholded_image_frame(thresholded_image_series[frame]))
        return labeled_image_series_list

    def give_regions_in_labeled_image_frame(self, labeled_frame, image_series_frame):
        regions = skimage.measure.regionprops(labeled_frame, intensity_image=image_series_frame)
        return regions

    def exclude_small_and_large_areas(self, raw_regions_in_frame, lower_limit_area, upper_limit_area):
        regions = [region for region in raw_regions_in_frame if lower_limit_area < region.area < upper_limit_area]
        return regions

    def measure_microdomains(self, image_series, threshold, lower_limit_area, upper_limit_area):
        """
        Measures the number and the intensites of microdomains in each frame of the ratio image and returns a dataframe
        :return:
        """
        thresholded_image_series = self.threshold_image_series(threshold, image_series)
        labels_for_each_frame = self.label_thresholded_image_series(thresholded_image_series)

        features = pd.DataFrame()
        for num, img in enumerate(image_series):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                if lower_limit_area < region.area < upper_limit_area:
                    features = features._append([{'y': region.centroid_weighted[0],
                                                  'x': region.centroid_weighted[1],
                                                  'time_in_seconds': float(num)/self.frames_per_second,
                                                  'area': region.area,
                                                  'max_intensity': region.intensity_max,
                                                  'min_intensity': region.intensity_min,
                                                  'mean_intensity': region.intensity_mean,

                                                  }, ])
        return features

    def track_hotspots(self, image_series, threshold, lower_limit_area, upper_limit_area):

        thresholded_image_series = self.threshold_image_series(threshold, image_series)

        labels_for_each_frame = self.label_thresholded_image_series(thresholded_image_series)

        features = pd.DataFrame()
        print("Track Hotspots")
        for num, img in tqdm(enumerate(image_series)):
            for region in skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img):
                if lower_limit_area < region.area < upper_limit_area:
                    features = features._append([{'y': region.centroid_weighted[0],
                                                  'x': region.centroid_weighted[1],
                                                  'time_in_seconds': float(num)/self.frames_per_second,
                                                  'area': region.area,
                                                  'max_intensity': region.intensity_max,
                                                  'min_intensity': region.intensity_min,
                                                  'mean_intensity': region.intensity_mean,

                                                  }, ])
        dataframe = None
        particle_set = None
        if (not features.empty):
            tp.annotate(features[features.time_in_seconds == (0)], image_series[0])
            # tracking, linking of coordinates
            search_range = 5  # TO DO: needs to be optimised!
            dataframe = tp.link_df(features, search_range, memory=0)
            dataframe = tp.filtering.filter_stubs(dataframe, threshold=3)
            particle_set = set(dataframe['particle'].tolist())
            if len(dataframe) > 0:
                tp.plot_traj(dataframe, superimpose=image_series[0])
        # print("features")
        # print(features)
        return dataframe, particle_set

    def calculate_number_of_connected_components(self, dataframe, time_in_seconds):
        subset = dataframe.loc[dataframe['time_in_seconds'] == time_in_seconds]
        return len(subset)

    # def save_dataframe_in_excel_file(self,dataframe,sheet_number, save_path):
    #     if dataframe is not None:
    #         dataframe.to_excel(self.excelwriter,sheet_name="Cell_image_" + str(sheet_number))
    #         dataframe.to_csv(save_path + "/Cell_image" + str(sheet_number))

    def count_microdomains_in_each_frame(self, dataframe):
        number_of_frames = len(set(dataframe['time_in_seconds'].tolist()))
        dataframe_copy = dataframe[['time_in_seconds']].copy()
        microdomains_in_each_frame = pd.DataFrame()

        for frame in range(number_of_frames):
            current_time_in_seconds = float(frame)/self.frames_per_second
            number_of_microdomains = len(dataframe_copy[dataframe_copy["time_in_seconds"]==current_time_in_seconds])
            microdomains_in_each_frame = microdomains_in_each_frame._append([{'time_in_seconds':
                                                                                  current_time_in_seconds,
                                                                              'number_of_microdomains': number_of_microdomains,
                                                                            }, ])
        return microdomains_in_each_frame


    def save_dataframes(self, dataframes_list):
        # Write to Multiple Sheets
        with pd.ExcelWriter(self.save_path + "/" + self.filename) as writer:
            index = 0

            for dataframe in dataframes_list:
                if (not dataframe.empty):
                    dataframe.to_excel(writer, sheet_name="Cell_RatioImage_" + str(index), index=False)
                    # print("dataframe")
                    # print(dataframe)
                    number_of_microdomains = self.count_microdomains_in_each_frame(dataframe)
                    number_of_microdomains.to_excel(writer, sheet_name="Cell_RatioImage_" + str(index) + "_Microdomains", index=False)
                    index += 1
