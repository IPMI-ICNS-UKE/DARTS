import pandas as pd
import trackpy as tp
import skimage
from tqdm import tqdm
import numpy as np


class HotSpotDetector():

    def __init__(self, save_path, results_folder, excel_filename_one_measurement, excel_filename_general, fps, ratioconverter, filename, scale_pixels_per_micron):
        self.save_path = save_path
        self.results_folder = results_folder
        self.excel_filename_one_measurement = excel_filename_one_measurement
        self.excel_filename_general = excel_filename_general

        self.frames_per_second = fps
        self.ratio_converter = ratioconverter
        self.file_name = filename
        self.scale_pixels_per_micron = scale_pixels_per_micron

    def threshold_image_frame(self, threshold, image_series, frame):
        thresholded_frame = image_series[frame] > threshold
        return thresholded_frame

    def threshold_image_series(self, threshold_list, image_series):
        thresholded_image = image_series.copy()
        frame_number = len(image_series)
        for frame in range(frame_number):
            thresholded_image[frame] = self.threshold_image_frame(threshold_list[frame], image_series, frame)
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
        regions = [region for region in raw_regions_in_frame if lower_limit_area <= region.area <= upper_limit_area]
        return regions

    def calculate_hotspot_threshold_for_each_frame(self, mean_ratio_list, cell_type, spotHeight):
        threshold_list = []
        for i in range(len(mean_ratio_list)):
            _, _, threshold_ratio = self.ratio_converter.calcium_calibration(mean_ratio_list[i],
                                                                          cell_type,
                                                                          spotHeight)
            threshold_list.append(threshold_ratio)
        return threshold_list


    def measure_microdomains(self, image_series, start_frame, end_frame, mean_ratio_value_list, spotHeight, lower_limit_area, upper_limit_area, cell_type, time_before_bead_contact):
        """
        Measures the number and the intensites of microdomains in each frame of the ratio image and returns a dataframe
        :return:
        """
        image_series_in_analysis_range = image_series[start_frame:end_frame,:,:].copy()
        hotspot_threshold_list = self.calculate_hotspot_threshold_for_each_frame(mean_ratio_value_list, cell_type, spotHeight)

        thresholded_image_series = self.threshold_image_series(hotspot_threshold_list, image_series_in_analysis_range)
        labels_for_each_frame = self.label_thresholded_image_series(thresholded_image_series)

        features = pd.DataFrame()
        for num, img in enumerate(image_series_in_analysis_range):
            regions = skimage.measure.regionprops(labels_for_each_frame[num], intensity_image=img)
            for region in regions:
                if lower_limit_area <= region.area <= upper_limit_area:
                    features = features._append([{'y': region.centroid_weighted[0],
                                                  'x': region.centroid_weighted[1],
                                                  'frame': num,
                                                  'time_in_seconds': float(num-time_before_bead_contact)/self.frames_per_second,
                                                  'area in (µm)^2': region.area / (self.scale_pixels_per_micron**2),
                                                  'max_intensity': region.intensity_max,
                                                  'min_intensity': region.intensity_min,
                                                  'mean_intensity': region.intensity_mean,
                                                  'max calcium concentration in nM': self.ratio_converter.calcium_calibration(region.intensity_max, cell_type)[0],
                                                  'min calcium concentration in nM': self.ratio_converter.calcium_calibration(region.intensity_min, cell_type)[0],
                                                  'mean calcium concentration in nM': self.ratio_converter.calcium_calibration(region.intensity_mean, cell_type)[0],

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
                                                  'area in (µm)^2': region.area / (self.scale_pixels_per_micron ** 2),
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

    def count_microdomains_in_each_frame(self, i, dataframe, number_of_frames, time_before_bead_contact, duration_of_measurement):
        microdomains_in_each_frame = pd.DataFrame()
        microdomains_timeline_for_cell = pd.DataFrame()

        for frame in range(time_before_bead_contact + duration_of_measurement):  # normally, 640 Frames
            if frame < number_of_frames:
                current_time_in_seconds = float(frame-time_before_bead_contact)/self.frames_per_second
                number_of_microdomains = len(dataframe[dataframe["time_in_seconds"] == current_time_in_seconds])
                microdomains_in_each_frame = microdomains_in_each_frame._append([{'time_in_seconds':
                                                                                      current_time_in_seconds,
                                                                                  'number_of_microdomains': number_of_microdomains,
                                                                                }, ])
                microdomains_timeline_for_cell = microdomains_timeline_for_cell._append([{self.file_name + "_cell_" + str(i): number_of_microdomains,
                                                                                }, ])
            else:
                current_time_in_seconds = float(frame - time_before_bead_contact) / self.frames_per_second
                number_of_microdomains = 0.0
                microdomains_in_each_frame = microdomains_in_each_frame._append([{'time_in_seconds':
                                                                                      current_time_in_seconds,
                                                                                  'number_of_microdomains': number_of_microdomains,
                                                                                  }, ])
                microdomains_timeline_for_cell = microdomains_timeline_for_cell._append(
                    [{self.file_name + "_cell_" + str(i): number_of_microdomains,
                      }, ])

        return microdomains_in_each_frame, microdomains_timeline_for_cell
# filename + "_cell_" + str(cell_index)

    def save_dataframes(self, file_name, index, cell_signal_data, number_of_analyzed_frames, time_before_bead_contact, duration_of_measurement):
        # Write to Multiple Sheets
        if not cell_signal_data.empty:
            with pd.ExcelWriter(self.save_path + "/" + self.excel_filename_one_measurement + '_cell_' + str(index) + '.xlsx') as writer:

                sheet_name = "Microdomains, cell " + str(index)
                cell_signal_data.to_excel(writer, sheet_name=sheet_name, index=False)
                number_of_microdomains, microdomains_timeline_for_cell = self.count_microdomains_in_each_frame(index, cell_signal_data, number_of_analyzed_frames, time_before_bead_contact, duration_of_measurement)
                sheet_name = "Microdomains per frame, cell " + str(index)
                number_of_microdomains.to_excel(writer, sheet_name=sheet_name, index=False)
                return microdomains_timeline_for_cell
        else:
            dataframe_with_zeros = pd.DataFrame()
            column_name = self.file_name + "_cell_" + str(index)
            for i in range(number_of_analyzed_frames):
                dataframe_with_zeros = dataframe_with_zeros._append(
                    [{column_name: 0,
                      }, ])
            return dataframe_with_zeros

