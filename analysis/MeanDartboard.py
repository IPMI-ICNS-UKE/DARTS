import os
import numpy as np
from analysis.Dartboard import DartboardGenerator

class MeanDartboardGenerator:
    def __init__(self, source_path, save_path, number_of_analyzed_cells, frame_rate, experiment_name, measurement_name, dartboard_sections, dartboard_areas_per_section):
        self.source_path = source_path
        self.save_path = save_path
        self.number_of_analyzed_cells = number_of_analyzed_cells
        self.frame_rate = frame_rate
        self.experiment_name = experiment_name
        self.measurement_name = measurement_name
        self.dartboard_sections = dartboard_sections
        self.dartboard_areas_per_section = dartboard_areas_per_section
        self.dartboard_generator = DartboardGenerator(self.save_path, self.frame_rate, self.measurement_name, self.experiment_name, self.save_path)

    def calculate_dartboard_data_for_all_cells(self):
        dartboard_data_array_list = []
        filename_list = os.listdir(self.source_path)
        filename_list = [file for file in filename_list if os.fsdecode(file).endswith(".npy")]

        for file in filename_list:
            array = np.load(self.source_path + '/' + file)
            dartboard_data_array_list.append(array)

        number_of_arrays = len(filename_list)  # divide by number of arrays to obtain mean dartboard data per cell and second for the whole measurement

        average_dartboard_data_per_cell_all_measurements = self.dartboard_generator.calculate_mean_dartboard_multiple_cells(
            self.number_of_analyzed_cells,
            dartboard_data_array_list,
            self.dartboard_sections,
            self.dartboard_areas_per_section,
            "Mean_dartboard",
            mean_dartboard_flag=True,
            number_arrays_mean_dartboard=number_of_arrays)


        # average_dartboard_data_all_measurements = np.divide(average_dartboard_data_all_measurements,4.0)  # temporaer
        self.dartboard_generator.save_dartboard_plot(average_dartboard_data_per_cell_all_measurements, self.number_of_analyzed_cells, self.dartboard_sections, self.dartboard_areas_per_section, vmax_plot = 9.61)
        # pass

"""
source_path = "/Users/dejan/Documents/GitHub/T-DARTS/results/KHYG-1 WT 4.8.2023/Part 1 variierte Beadkontakte/Dartboards/Dartboard 40-200/source"
save_path = "/Users/dejan/Documents/GitHub/T-DARTS/results/KHYG-1 WT 4.8.2023/Part 1 variierte Beadkontakte/Dartboards/Dartboard 40-200/save"
number_of_analyzed_cells = 7
frame_rate = 40.0
experiment_name = "NK_cells_4_sec"
measurement_name = "test"
dartboard_sections = 12
dartboard_areas_per_section = 8
dartboard_gen = MeanDartboardGenerator(source_path, save_path, number_of_analyzed_cells, frame_rate, experiment_name, measurement_name, dartboard_sections, dartboard_areas_per_section)

dartboard_gen.calculate_dartboard_data_for_all_cells()
"""
