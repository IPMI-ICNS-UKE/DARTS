import math
import numpy as np
import matplotlib.pyplot as plt
import os

class DartboardGenerator:
    def __init__(self, save_path):
        self.save_path = save_path

    def execute(self, channel, parameters):
        print(self.give_name())
        return self.apply_dartboard_on_membrane(channel, parameters)

    def generate_dartboard(self, ratio_image_frame, number_of_areas, edge_coord_list, radius_inner_circle):
        dartboard_area_list = []

        return dartboard_area_list

    def distance_from_pixel_to_center(self, signal_coords, centroid_coords):
        delta_x = float(centroid_coords[1]) - signal_coords[1]
        delta_y = float(centroid_coords[0]) - signal_coords[0]
        distance = math.sqrt(delta_x**2 + delta_y**2)
        return distance

    def calculate_signal_angle_relative_to_center(self, centroid_coords, signal_coords):
        y0 = centroid_coords[0]
        x0 = centroid_coords[1]
        x = signal_coords[0]
        y = signal_coords[1]
        angle = (math.degrees(math.atan2(y0 - y, x0 - x)) + 180)% 360
        return angle

    def assign_angle_to_dartboard_section(self, angle, number_of_areas):
        angle_one_section = 360.0 / number_of_areas
        dartboard_section = int(angle / angle_one_section)
        return dartboard_section

    def  assign_signal_to_nth_area(self, distance_from_center, radius_cell_image, areas_height, number_of_areas_in_one_section):
        # interval = radius_cell_image / (number_of_areas_in_one_section - 1.0)
        interval = radius_cell_image / (areas_height*number_of_areas_in_one_section)
        dartboard_area = int(distance_from_center/interval)
        if(radius_cell_image < distance_from_center < 0):
            return -1
        else:
            return dartboard_area

    def assign_signal_to_dartboard_area(self, signal_coords, centroid_coords, number_of_sections, number_of_areas_in_one_section, radius_cell_image):
        if radius_cell_image < self.distance_from_pixel_to_center(signal_coords, centroid_coords): #< radius_inner_circle:
            return None,None
        else:
            # angle_one_dartboard_area = 360.0/number_of_sections
            angle = self.calculate_signal_angle_relative_to_center(centroid_coords, signal_coords)
            dartboard_section = self.assign_angle_to_dartboard_section(angle, number_of_sections)
            distance_to_center = self.distance_from_pixel_to_center(signal_coords, centroid_coords)
            dartboard_area_number_within_section = self.assign_signal_to_nth_area(distance_to_center,
                                                                                  radius_cell_image,
                                                                                  1,
                                                                                  number_of_areas_in_one_section)

            return dartboard_section, dartboard_area_number_within_section

    def count_signals_in_each_dartboard_area_in_one_frame(self, frame, dataframe, centroid_coords, number_of_sections, number_of_areas_within_section, radius_cell_image):
        dartboard_area_frequency = np.zeros(shape=(number_of_areas_within_section, number_of_sections))

        dataframe_one_frame = self.reduce_dataframe_to_one_frame(dataframe, frame)
        signal_in_frame_coords_list = self.extract_signal_coordinates_from_one_frame(dataframe_one_frame)

        for signal in signal_in_frame_coords_list:
            x = signal[0]
            y = signal[1]
            signal_coords = (x, y)
            dartboard_section, dartboard_area_number_within_section = self.assign_signal_to_dartboard_area(signal_coords,
                                                                                                           centroid_coords,
                                                                                                           number_of_sections,
                                                                                                           number_of_areas_within_section,
                                                                                                           radius_cell_image)
            if(dartboard_section is not None and dartboard_area_number_within_section is not None):
                dartboard_area_frequency[dartboard_area_number_within_section][dartboard_section] += 1

        return dartboard_area_frequency

    def reduce_dataframe_to_one_frame(self, signal_dataframe, frame):
        subset = signal_dataframe.loc[signal_dataframe['frame'] == frame]
        return subset

    def extract_signal_coordinates_from_one_frame(self, dataframe_subset):
        x_values = dataframe_subset['x'].to_numpy().tolist()
        y_values = dataframe_subset['y'].to_numpy().tolist()
        signals_coords_list_in_one_frame = list(zip(x_values, y_values))
        return signals_coords_list_in_one_frame

    def calculate_signals_in_dartboard_each_frame(self, number_of_frames, signal_dataframe, number_of_dartboard_sections, number_of_dartboard_areas_per_section, list_of_centroid_coords, radius_cell_image, cell_index):
        dartboard_area_frequencies = []
        for frame in range(number_of_frames):
            centroid_coords = list_of_centroid_coords[frame]
            dartboard_area_frequency_this_frame = self.count_signals_in_each_dartboard_area_in_one_frame(frame,
                                                                                                         signal_dataframe,
                                                                                                         centroid_coords,
                                                                                                         number_of_dartboard_sections,
                                                                                                         number_of_dartboard_areas_per_section,
                                                                                                         radius_cell_image)

            # self.plot_dartboard(dartboard_area_frequency_this_frame, radius_cell_image, cell_index, frame)
            dartboard_area_frequencies.append(dartboard_area_frequency_this_frame)
        return dartboard_area_frequencies


    def calculate_mean_dartboard(self, dartboard_area_frequencies, start_frame, end_frame,number_of_sections, number_of_areas_within_section):
        if(len(dartboard_area_frequencies)>0):
            sub_list = dartboard_area_frequencies[start_frame:end_frame]
            number_of_frames = float(len(sub_list))
            average_array = np.zeros_like(dartboard_area_frequencies[0])
            for array in sub_list:
                for y in range(len(array)):
                    for x in range(len(array[0])):
                        average_array[y][x] += array[y][x]
            average_array = average_array / number_of_frames
            return average_array
        else:
            average_array = np.zeros(shape=(number_of_areas_within_section, number_of_sections))
            return average_array


    def normalize_average_dartboard_data_one_cell(self, average_dartboard_data, real_bead_contact_site, normalized_bead_contact_site):
        difference = real_bead_contact_site - normalized_bead_contact_site
        return self.rotate_dartboard_data_counterclockwise(average_dartboard_data,difference)

    def rotate_dartboard_data_counterclockwise(self, dartboard_data, n):
        dartboard_data_copy = dartboard_data.copy()
        for elem in range(len(dartboard_data_copy)):
            dartboard_data_copy[elem] = np.roll(dartboard_data_copy[elem],n)
        return dartboard_data_copy


    def save_dartboard_plot(self, dartboard_data, number_of_cells, number_of_sections, number_of_areas_per_section):

        red_sequential_cmap = plt.get_cmap("Reds")
        # red_colors = (np.linspace(0, 2.0, 16))

        fig = plt.figure()
        ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)

        number_of_sections = number_of_sections
        number_of_areas_in_section = number_of_areas_per_section
        angle_per_section = 360.0 / number_of_sections

        for i in range(number_of_sections):
            center_angle = math.radians((i * angle_per_section + angle_per_section / 2) % 360.0)

            for dartboard_area in range(number_of_areas_in_section):
                if (dartboard_area>4):
                    number_of_signals_in_current_dartboard_area = dartboard_data[dartboard_area][i]

                    color = red_sequential_cmap(number_of_signals_in_current_dartboard_area)  # nur vorübergehend

                    ax.bar(x=center_angle, height=1, width=2 * np.pi / (number_of_sections), bottom=dartboard_area,
                           color=color, edgecolor='white')

        plt.ylim(0, 8)

        ax.grid(False)

        ax.set_yticks([])
        ax.axis("off")

        image_identifier = "Activity map (" + str(number_of_cells) + " cells)" # + " - start frame: " + str(start_frame) + " - end frame: " + str(end_frame)
        plt.title(image_identifier)
        sm = plt.cm.ScalarMappable(cmap=red_sequential_cmap)
        sm.set_clim(vmin=0, vmax=2.0)
        plt.colorbar(sm, pad=0.3)

        ax.annotate('Bead contact',
                    xy=(math.radians(45), 8),  # theta, radius
                    xytext=(0.6, 0.85),  # fraction, fraction
                    textcoords='figure fraction',
                    arrowprops=dict(facecolor='black', shrink=0.05, width=0.5),
                    horizontalalignment='left',
                    verticalalignment='bottom',
                    )


        directory = self.save_path + '/Dartboard_plots/cell_number_' + image_identifier + '/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        plt.savefig(directory + image_identifier + '.tiff', dpi=300)
        # plt.show()

