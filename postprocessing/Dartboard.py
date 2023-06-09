import math
import numpy as np

class DartboardGenerator:
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
        angle = math.degrees(math.atan2(y0 - y, x0 - x)) % 360
        return angle

    def assign_signal_to_dartboard_area(self, signal_coords, centroid_coords, number_of_areas, radius_inner_circle, radius_outer_circle):
        if radius_outer_circle < self.distance_from_pixel_to_center(signal_coords, centroid_coords) < radius_inner_circle:
            return -1
        else:
            angle_one_dartboard_area = 360.0/number_of_areas
            angle = self.calculate_signal_angle_relative_to_center(centroid_coords, signal_coords)
            number_of_dartboard_area = int(angle/angle_one_dartboard_area)
            return number_of_dartboard_area


    def count_signals_in_each_dartboard_area_in_one_frame(self, frame, dataframe, centroid_coords, number_of_dartboard_areas, radius_inner_circle):
        dartboard_area_frequency = {}
        for i in range(number_of_dartboard_areas):
            dartboard_area_frequency[i] = 0
        dataframe_one_frame = self.reduce_dataframe_to_one_frame(dataframe, frame)
        signal_in_frame_coords_list = self.extract_signal_coordinates_from_one_frame(dataframe_one_frame)


        for signal in signal_in_frame_coords_list:
            x = signal[0]
            y = signal[1]
            signal_coords = (x, y)
            number_of_dartboard_area = self.assign_signal_to_dartboard_area(signal_coords,
                                                                            centroid_coords,
                                                                            number_of_dartboard_areas,
                                                                            radius_inner_circle)
            if number_of_dartboard_area is not None:
                dartboard_area_frequency[number_of_dartboard_area] +=1
        return dartboard_area_frequency

    def reduce_dataframe_to_one_frame(self, signal_dataframe, frame):
        subset = signal_dataframe.loc[signal_dataframe['frame'] == frame]
        return subset

    def extract_signal_coordinates_from_one_frame(self, dataframe_subset):
        x_values = dataframe_subset['x'].to_numpy().tolist()
        y_values = dataframe_subset['y'].to_numpy().tolist()
        signals_coords_list_in_one_frame = list(zip(x_values, y_values))
        return signals_coords_list_in_one_frame

    def calculate_signals_in_dartboard_each_frame(self, number_of_frames, signal_dataframe, number_of_dartboard_areas, list_of_centroid_coords, radius_inner_circle):
        dartboard_area_frequency = []
        for frame in range(number_of_frames):
            centroid_coords = list_of_centroid_coords[frame]
            frame_dartboard_area_frequency = self.count_signals_in_each_dartboard_area_in_one_frame(frame,
                                                                                                    signal_dataframe,
                                                                                                    centroid_coords,
                                                                                                    number_of_dartboard_areas,
                                                                                                    radius_inner_circle
                                                                                                    )
            print(frame_dartboard_area_frequency)


    def create_dartboard_image(self,frame_image, number_of_areas, centroid_coords, radius_inner_circle,radius_outer_circle,dartboard_information_dict):
        dartboard_image = np.zeros_like(frame_image)


        for row in range(len(frame_image)):
            for col in range(len(frame_image[0])):

                dartboard_index_of_pixel = self.assign_signal_to_dartboard_area((col, row),
                                                                                centroid_coords,
                                                                                number_of_areas,
                                                                                radius_inner_circle,
                                                                                radius_outer_circle)
                if (dartboard_index_of_pixel > -1):
                    dartboard_image[row][col] = self.calculate_pixel_intensity(dartboard_index_of_pixel,dartboard_information_dict)
                else:
                    dartboard_image[row][col] = 0
        return dartboard_image

    def calculate_pixel_intensity(self, dartboard_index, dartboard_information_dict):
        pixel_intensity = dartboard_information_dict[dartboard_index] * 100
        return pixel_intensity


# {0: 1, 1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 0, 7: 0}
# {0: 1, 1: 2, 2: 1, 3: 1, 4: 1, 5: 3, 6: 0, 7: 0}



import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

size = 0.3
vals = np.array([[60., 10.], [60., 10.], [60., 10.]])

cmap = plt.colormaps["tab20c"]
outer_colors = cmap(np.arange(3)*4)

ax.pie(vals.sum(axis=1), radius=1, colors=outer_colors,
       wedgeprops=dict(width=size, edgecolor='w'),startangle=90)


ax.set(aspect="equal", title='Dartboard projection')
plt.show()