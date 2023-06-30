from tkinter import filedialog as fd
import numpy as np
from analysis.Dartboard import DartboardGenerator
import os

def give_list_of_average_dartboard_data_array():

    directory = fd.askdirectory()
    average_dartboard_data = []

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".npy"):
            average_array = np.load(directory + '/' + filename)
            average_dartboard_data.append(average_array)
    return average_dartboard_data, directory

def create_average_dartboard_for_n_cells(number_of_cells, list_of_average_dartboard_data, save_path, frame_rate, measurement_name, experiment_name, results_folder):
    dartboard_generator = DartboardGenerator(save_path, frame_rate, measurement_name, experiment_name, results_folder)
    average_dartboard_data_all_cells = dartboard_generator.calculate_mean_dartboard_multiple_cells(number_of_cells,
                                                                                                   list_of_average_dartboard_data,
                                                                                                   12,
                                                                                                   8,
                                                                                                   save_dartboard_data=False)
    dartboard_generator.save_dartboard_plot(average_dartboard_data_all_cells, number_of_cells, 12, 8)


average_dartboard_data_list, directory = give_list_of_average_dartboard_data_array()
save_path = directory
frame_rate = 40
day_of_measurement = "2023-06-26"
experiment_name = "WT OKT3"
measurement_name = day_of_measurement + '_' + experiment_name

create_average_dartboard_for_n_cells(2, average_dartboard_data_list, save_path, frame_rate, measurement_name, experiment_name, save_path)



