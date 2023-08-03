import numpy as np
import pandas as pd
from analysis.MeanDartboard import MeanDartboardGenerator
import os


class InfoToComputer:
    def __init__(self, parameters):
        self.dartboard_data_list = []
        self.bead_contact_dict = {}
        self.save_path = parameters["inputoutput"]["path_to_output"] + '/'
        self.number_of_analyzed_cells_in_total = 0
        self.number_of_responding_cells_in_total = 0
        self.general_mean_amplitude_list = []
        self.parameters = parameters

        self.number_of_signals_per_frame = pd.DataFrame()
        fps = parameters["properties"]["frames_per_second"]
        duration_of_measurement_in_frames = int(16 * fps)  # from 1s before bead contact to 15s after bead contact
        list_of_time_points = []
        for frame in range(duration_of_measurement_in_frames):
            time_in_seconds = (frame - fps) / fps
            list_of_time_points.append(time_in_seconds)

        self.number_of_signals_per_frame['time_in_seconds'] = list_of_time_points

        self.selected_dartboard_areas = self.parameters["properties"]["selected_dartboard_areas_for_timeline"]
        self.timeline_single_dartboard_areas = pd.DataFrame()
        if self.selected_dartboard_areas:  # if not empty
            for frame in range(int(16*fps)):  # only after bead contact
                time_in_seconds = (frame - fps) / fps
                new_row = {'frame': int(frame),
                           'time_in_seconds': time_in_seconds}
                for selected_area in self.selected_dartboard_areas:
                    new_row[str(selected_area)] = 0.0
                new_row['sum'] = 0.0
                self.timeline_single_dartboard_areas = self.timeline_single_dartboard_areas._append(new_row, ignore_index=True)

    def save_bead_contact_information(self):
        with open(self.save_path + 'Bead_contact_information.txt', 'w') as f:
            for file in self.bead_contact_dict:
                f.write("Filename: " + file + "\n")
                for bead_contact in self.bead_contact_dict[file]:
                    f.write(" Bead contact: " + bead_contact.to_string() + "\n")
                f.write("\n")

    def save_number_of_responding_cells(self):
        with open(self.save_path + 'Number of responding cells.txt', 'w') as f:
            f.write("Number of analyzed cells in total: " + str(self.number_of_analyzed_cells_in_total) + "\n")
            f.write("Number of analyzed cells with hotspots in total: " + str(
                self.number_of_responding_cells_in_total) + "\n")
            if self.number_of_analyzed_cells_in_total != 0:
                percentage_of_responding_cells = float(
                    self.number_of_responding_cells_in_total) / self.number_of_analyzed_cells_in_total * 100
            else:
                percentage_of_responding_cells = 0
            f.write("Percentage of responding cells: " + str(percentage_of_responding_cells) + "%")

    def create_general_dartboard(self):
        fps = self.parameters["properties"]["frames_per_second"]
        experiment_name = self.parameters["inputoutput"]["experiment_name"]
        dartboard_sections = self.parameters["properties"]["dartboard_number_of_sections"]
        dartboard_areas_per_section = self.parameters["properties"]["dartboard_number_of_areas_per_section"]

        source_path = self.save_path + 'Dartboard_data_all_files'
        os.makedirs(source_path, exist_ok=True)
        measurement_name = "dartboard_for_all_analyzed_cells"

        mean_dartboard_generator = MeanDartboardGenerator(source_path, self.save_path, self.number_of_analyzed_cells_in_total, fps,
                                                          experiment_name, measurement_name, dartboard_sections,
                                                          dartboard_areas_per_section)
        mean_dartboard_generator.calculate_dartboard_data_for_all_cells()

    def save_number_of_signals(self):
        excel_filename_general = self.parameters["inputoutput"]["excel_filename_all_cells"]
        with pd.ExcelWriter(self.save_path + excel_filename_general) as writer:
            sheet_name = "Number of signals in each frame"
            self.number_of_signals_per_frame.to_excel(writer, sheet_name=sheet_name, index=False)

    def add_signal_information(self, microdomains_timelines_dict):
        for filename_cell in microdomains_timelines_dict:
            filename = filename_cell[0]
            cell_index = filename_cell[1]
            title_of_microdomains_timeline = filename + "_cell_" + str(cell_index)

            dataframe_series = microdomains_timelines_dict[filename_cell]
            self.number_of_signals_per_frame[title_of_microdomains_timeline] = dataframe_series[title_of_microdomains_timeline].tolist()

    def save_mean_amplitudes(self):
        with open(self.save_path + "Mean amplitudes of responding cells.txt", "a") as f:
            for mean_amplitude in self.general_mean_amplitude_list:
                f.write(str(mean_amplitude) + " nM\n")

    def adapt_timeline_data(self):
        sum = np.zeros(len(self.timeline_single_dartboard_areas.index))
        for selected_area in self.selected_dartboard_areas:
            values_as_array = self.timeline_single_dartboard_areas[str(selected_area)].to_numpy()
            divided_by_cell_number = np.divide(values_as_array, self.number_of_analyzed_cells_in_total)
            sum = np.add(sum, divided_by_cell_number)
            self.timeline_single_dartboard_areas[str(selected_area)] = divided_by_cell_number.tolist()
        if not self.timeline_single_dartboard_areas.empty:
            self.timeline_single_dartboard_areas['sum'] = sum.tolist()
        self.change_column_names_timeline_data()

    def change_column_names_timeline_data(self):
        changed_names_dict = {}
        for selected_area in self.selected_dartboard_areas:
            corresponding_name = self.generate_corresponding_name(selected_area)
            changed_names_dict[str(selected_area)] = corresponding_name

        self.timeline_single_dartboard_areas = self.timeline_single_dartboard_areas.rename(columns=changed_names_dict)

    def generate_corresponding_name(self, selected_dartboard_area):
        list = ['3', '2', '1', '12', '11', '10', '9', '8', '7', '6', '5', '4']
        clock = list[selected_dartboard_area[0]] + ' o\'clock, '
        ring = ""
        if selected_dartboard_area[1] == 5:
            ring = 'inner ring'
        elif selected_dartboard_area[1] == 6:
            ring = 'middle ring'
        elif selected_dartboard_area[1] == 7:
            ring = 'outer ring'

        return clock + ring

    def save_timelines_for_single_dartboard_areas(self):
        if not self.timeline_single_dartboard_areas.empty:
            with pd.ExcelWriter(self.save_path + '/Dartboards/Dartboard_data/timelines_dartboard.xlsx') as writer:
                sheet_name = "No. of hotspots per frame"

                self.timeline_single_dartboard_areas.to_excel(writer, sheet_name=sheet_name, index=False)
