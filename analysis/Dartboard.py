import math
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import colors
import matplotlib as mpl
import os
import pandas as pd


class DartboardGenerator:
    def __init__(self, save_path, frame_rate, measurement_name, experiment_name, results_folder):
        self.save_path = save_path
        self.frames_per_second = frame_rate
        self.measurement_name = measurement_name
        self.experiment_name = experiment_name
        self.results_folder = results_folder


    def distance_from_pixel_to_center(self, signal_coords, centroid_coords):
        delta_x = float(centroid_coords[0]) - signal_coords[0]
        delta_y = float(centroid_coords[1]) - signal_coords[1]
        distance = math.sqrt(delta_x**2 + delta_y**2)
        return distance

    def calculate_signal_angle_relative_to_center(self, centroid_coords, signal_coords):
        x0 = centroid_coords[0]
        y0 = centroid_coords[1]
        x = signal_coords[0]
        y = signal_coords[1]

        angle = (math.degrees(math.atan2(-(y0 - y), x0 - x)) + 180) % 360

        return angle

    def assign_angle_to_dartboard_section(self, angle, number_of_sections):
        angle_one_section = 360.0 / number_of_sections
        dartboard_section = int(angle / angle_one_section)
        # list = [3,2,1,12,11,10,9,8,7,6,5,4]
        return dartboard_section

    def assign_signal_to_nth_area(self, distance_from_center, radius_cell_image, number_of_areas_in_one_section):
        # height_of_annuli = [0, 0, 0, 0, 0, 2, 1.544, 1.3049]  # manually calculated, so that the areas of the dartboard areas all have the area 2pi
        bottom_list = [5, 7, 8.544, 9.8489]
        radius_dartboard = 9.8489

        normalized_distance_of_signal_from_center = (distance_from_center / radius_cell_image) * radius_dartboard
        if 0 < normalized_distance_of_signal_from_center <= bottom_list[0]:
            return 4  # equivalent to bull's eye
        elif bottom_list[0] < normalized_distance_of_signal_from_center <= bottom_list[1]:
            return 5
        elif bottom_list[1] < normalized_distance_of_signal_from_center <= bottom_list[2]:
            return 6
        elif bottom_list[2] < normalized_distance_of_signal_from_center <= bottom_list[3]:
            return 7
        else:
            return -1

    def assign_signal_to_dartboard_area(self, signal_coords, centroid_coords, number_of_sections, number_of_areas_in_one_section, radius_cell_image):
        if radius_cell_image < self.distance_from_pixel_to_center(signal_coords, centroid_coords): #< radius_inner_circle:
            return None, None
        else:
            # angle_one_dartboard_area = 360.0/number_of_sections
            angle = self.calculate_signal_angle_relative_to_center(centroid_coords, signal_coords)
            dartboard_section = self.assign_angle_to_dartboard_section(angle, number_of_sections)
            distance_to_center = self.distance_from_pixel_to_center(signal_coords, centroid_coords)
            dartboard_area_number_within_section = self.assign_signal_to_nth_area(distance_to_center,
                                                                                  radius_cell_image,
                                                                                  number_of_areas_in_one_section)

            return dartboard_section, dartboard_area_number_within_section

    def count_signals_in_each_dartboard_area_in_one_frame(self, frame, dataframe, centroid_coords, number_of_sections, number_of_areas_within_section, radius_cell_image):
        if not dataframe.empty:
            dartboard_area_frequency = np.zeros(shape=(number_of_areas_within_section, number_of_sections))

            dataframe_one_frame = self.reduce_dataframe_to_one_frame(dataframe, frame)
            signal_in_frame_coords_list = self.extract_signal_coordinates_from_one_frame(dataframe_one_frame)

            for signal in signal_in_frame_coords_list:
                dartboard_section, dartboard_area_number_within_section = self.assign_signal_to_dartboard_area(signal,
                                                                                                               centroid_coords,
                                                                                                               number_of_sections,
                                                                                                               number_of_areas_within_section,
                                                                                                               radius_cell_image)
                if(dartboard_section is not None and dartboard_area_number_within_section is not None):
                    dartboard_area_frequency[dartboard_area_number_within_section][dartboard_section] += 1

            return dartboard_area_frequency
        else:
            dartboard_area_frequency = np.zeros(shape=(number_of_areas_within_section, number_of_sections))
            return dartboard_area_frequency

    def reduce_dataframe_to_one_frame(self, signal_dataframe, frame):
        subset = signal_dataframe.loc[signal_dataframe['frame'] == frame].copy()
        return subset

    def extract_signal_coordinates_from_one_frame(self, dataframe_subset):
        x_values = dataframe_subset['x'].to_numpy().tolist()
        y_values = dataframe_subset['y'].to_numpy().tolist()
        signals_coords_list_in_one_frame = list(zip(x_values, y_values))
        return signals_coords_list_in_one_frame

    def cumulate_dartboard_data_multiple_frames(self, signal_dataframe, number_of_dartboard_sections, number_of_dartboard_areas_per_section, list_of_centroid_coords, radii_after_normalization, cell_index, time_of_bead_contact, start_frame, end_frame, selected_dartboard_areas, timeline_single_dartboard_areas, cell):
        cumulated_dartboard_data = np.zeros(shape=(number_of_dartboard_areas_per_section, number_of_dartboard_sections)).astype(float)

        dartboard_timeline_data_single_cell = timeline_single_dartboard_areas.copy()  # better: initialize with zeros or NaN

        for frame in range(start_frame, end_frame):
            centroid_coords = list_of_centroid_coords[frame]
            current_radius = radii_after_normalization[frame] + 2  # 2 as correction term; rather have to large radius than lose information. Sometimes, the circle does not contain all the pixels.
            normalized_frame = frame - start_frame
            dartboard_area_frequency_this_frame = self.count_signals_in_each_dartboard_area_in_one_frame(normalized_frame,
                                                                                                         signal_dataframe,
                                                                                                         centroid_coords,
                                                                                                         number_of_dartboard_sections,
                                                                                                         number_of_dartboard_areas_per_section,
                                                                                                         current_radius)
            if frame >= time_of_bead_contact:
                cumulated_dartboard_data = np.add(cumulated_dartboard_data, dartboard_area_frequency_this_frame)

            # normalize the dartboard data for this frame, because the bead contact site might differ from the later normalized site:
            normalized_dartboard_data = self.normalize_dartboard_data_to_bead_contact(
                dartboard_area_frequency_this_frame.copy(), cell.bead_contact_site, 2)

            sum = 0
            for selected_area in selected_dartboard_areas:
                selected_dartboard_section_index = selected_area[0]

                selected_dartboard_area_within_section_index = selected_area[1]

                number_of_signals_in_selected_area = normalized_dartboard_data[selected_dartboard_area_within_section_index][selected_dartboard_section_index]

                timeline_single_dartboard_areas.at[
                    int(frame - start_frame), str(selected_area)] += number_of_signals_in_selected_area

                dartboard_timeline_data_single_cell.at[
                    int(frame - start_frame), str(selected_area)] = number_of_signals_in_selected_area
                sum += number_of_signals_in_selected_area

            dartboard_timeline_data_single_cell.at[int(frame-start_frame), 'sum'] = sum

        cell.dartboard_timeline_data = dartboard_timeline_data_single_cell

        return cumulated_dartboard_data

    def calculate_mean_dartboard_multiple_cells(self, number_of_cells, dartboard_area_frequencies,number_of_sections, number_of_areas_within_section, filename):
        if(len(dartboard_area_frequencies)>0):
            number_of_cells = float(number_of_cells)

            average_array = np.zeros_like(dartboard_area_frequencies[0]).astype(float)
            for array in dartboard_area_frequencies:
                average_array = np.add(average_array, array)
            average_array = np.divide(average_array, number_of_cells)
            save_path = self.save_path + '/Dartboards/Dartboard_data/'
            os.makedirs(save_path, exist_ok=True)
            np.save(save_path + filename + '_' + str(int(number_of_cells)) + '_cells', average_array)

            cumulated_data_folder = self.results_folder + '/Dartboard_data_all_files'
            os.makedirs(cumulated_data_folder, exist_ok=True)
            np.save(cumulated_data_folder + '/' + filename + '_' + str(int(number_of_cells)) + '_cells', average_array)

            return average_array
        else:
            average_array = np.zeros(shape=(number_of_areas_within_section, number_of_sections))
            return average_array

    def save_dartboard_data_for_single_cell(self, dartboard_data_filename, dartboard_data, cell):
        save_path = self.save_path + '/Dartboards/Dartboard_data/'
        os.makedirs(save_path, exist_ok=True)
        np.save(save_path + dartboard_data_filename, dartboard_data)

        if not cell.dartboard_timeline_data.empty:
            with pd.ExcelWriter(save_path + dartboard_data_filename + '_timelines.xlsx') as writer:
                sheet_name = "dartboard timelines"
                cell.dartboard_timeline_data.to_excel(writer, sheet_name=sheet_name, index=False)


    def normalize_dartboard_data_to_bead_contact(self, dartboard_data, real_bead_contact_site, normalized_bead_contact_site):
        difference = real_bead_contact_site - normalized_bead_contact_site
        return self.rotate_dartboard_data_counterclockwise(dartboard_data, difference)


    def rotate_dartboard_data_counterclockwise(self, dartboard_data, n):
        dartboard_data_copy = dartboard_data.copy()
        for elem in range(len(dartboard_data_copy)):
            dartboard_data_copy[elem] = np.roll(dartboard_data_copy[elem],n)
        return dartboard_data_copy


    def save_dartboard_plot(self, dartboard_data, number_of_cells, number_of_sections, number_of_areas_in_section):
        vmin = 0
        vmax = 0.2
        dartboard_data_per_second = dartboard_data
        # dartboard_data_per_frame = dartboard_data_per_second / self.frames_per_second


        # red_sequential_cmap = plt.get_cmap("Reds")
        normalized_color = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
        white_to_red_cmap = colors.LinearSegmentedColormap.from_list("", ["white","red"])



        fig = plt.figure()
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)

        angle_per_section = 360.0 / number_of_sections

        height_of_annuli = [0, 0, 0, 0, 0, 2, 1.544, 1.3049]  # manually calculated, so that the areas of the dartboard areas all have the area 2pi
        bottom_list = [0, 0, 0, 0, 0, 5, 7, 8.544, 9.8489]
        area_of_one_dartboard_area = (7**2*math.pi - 5**2*math.pi)*angle_per_section/360.0
        area_of_bulls_eye = 5**2*math.pi
        area_ratio_bulls_eye_dartboard_area = area_of_bulls_eye / area_of_one_dartboard_area


        # create bull's eye
        number_of_signals_in_bulls_eye = 0
        for i in range(5):
            number_of_signals_in_bulls_eye += np.sum(dartboard_data_per_second[i])
        normalized_number_of_signals = number_of_signals_in_bulls_eye / area_ratio_bulls_eye_dartboard_area

        color = white_to_red_cmap(normalized_color(normalized_number_of_signals))


        ax.bar(x=0, height=5, width=2 * np.pi,
               bottom=0,
               color=color)


        # create dartboard areas outside of bull's eye
        for i in range(number_of_sections):
            center_angle = math.radians((i * angle_per_section + angle_per_section / 2) % 360.0)

            for dartboard_area in range(number_of_areas_in_section):
                if (dartboard_area>4):
                    number_of_signals_in_current_dartboard_area = dartboard_data_per_second[dartboard_area][i]

                    color = white_to_red_cmap(normalized_color(number_of_signals_in_current_dartboard_area))

                    ax.bar(x=center_angle, height=height_of_annuli[dartboard_area], width=2 * np.pi / (number_of_sections), bottom=bottom_list[dartboard_area],
                           color=color, edgecolor='white')

        plt.ylim(0, 9.85)

        ax.grid(False) # test

        ax.set_yticks([])
        ax.axis("on")  # test
        ax.set_xticks([])

        image_identifier = self.measurement_name + 'average_dartboard_plot_' + str(int(number_of_cells)) + '_cells'

        plt.title('Activity map: ' + str(int(number_of_cells)) + ' cell(s)', x=0.5, y=1.15)


        sm = plt.cm.ScalarMappable(cmap=white_to_red_cmap, norm=normalized_color)
        sm.set_clim(vmin=vmin, vmax=vmax)
        plt.colorbar(sm, pad=0.3, label="number of hotspots per second and area unit; \naveraged over cells")


        ax.annotate('Bead contact',
                    xy=(math.radians(45), 9.85),  # theta, radius
                    xytext=(0.6, 0.85),  # fraction, fraction
                    textcoords='figure fraction',
                    arrowprops=dict(facecolor='black', shrink=0.05, width=0.5),
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    )

        directory = self.save_path + '/Dartboards/Dartboard_plots/'

        if not os.path.exists(directory):
            os.makedirs(directory)

        plt.savefig(directory + image_identifier + '.tiff', dpi=1200)
