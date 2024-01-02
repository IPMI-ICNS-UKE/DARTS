import pandas as pd
import os


class InfoToComputer:
    def __init__(self, parameters):
        self.dartboard_data_list = []
        # self.dartboard_data_cumulated_all_cells = np.zeros(shape=(parameters["properties"]["dartboard_number_of_areas_per_section"],parameters["properties"]["dartboard_number_of_sections"])).astype(float)
        self.analyzed_seconds_cumulated = 0.0
        self.bead_contact_dict = {}
        self.save_path = parameters["input_output"]["results_dir"] + '/'
        self.number_of_analyzed_cells_in_total = 0
        self.number_of_responding_cells_in_total = 0
        self.general_mean_amplitude_list = []
        self.parameters = parameters

        self.number_of_signals_per_frame = pd.DataFrame()
        fps = parameters["properties_of_measurement"]["frame_rate"]
        time_before = parameters["properties_of_measurement"]["time_of_measurement_before_starting_point"]
        time_after = parameters["properties_of_measurement"]["time_of_measurement_after_starting_point"]
        duration_of_measurement_in_seconds = time_before + time_after
        duration_of_measurement_in_frames = int(duration_of_measurement_in_seconds * fps)
        list_of_time_points = []
        for frame in range(duration_of_measurement_in_frames):
            time_in_seconds = (frame - (time_before*fps)) / fps
            list_of_time_points.append(time_in_seconds)

        self.number_of_signals_per_frame['time_in_seconds'] = list_of_time_points

        self.global_data = pd.DataFrame()
        self.global_data['time_in_seconds'] = list_of_time_points.copy()

    def save_global_data(self):
        save_path = self.save_path + '/global_data'
        os.makedirs(save_path, exist_ok=True)

        with pd.ExcelWriter(save_path + '/global_data.xlsx') as writer:
            sheet_name = "global data all cells"
            self.global_data.to_excel(writer, sheet_name=sheet_name, index=False)

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

    def save_number_of_signals(self):
        excel_filename_general = self.parameters["input_output"]["excel_filename_microdomain_data"]
        with pd.ExcelWriter(self.save_path + excel_filename_general) as writer:
            sheet_name = "Number of signals in each frame"
            self.number_of_signals_per_frame.to_excel(writer, sheet_name=sheet_name, index=False)

    def add_signal_information(self, microdomains_timelines_dict):
        for filename_cell in microdomains_timelines_dict:
            filename = filename_cell[0]
            cell_index = filename_cell[1]
            title_of_microdomains_timeline = filename + "_cell_" + str(cell_index)

            dataframe_series = microdomains_timelines_dict[filename_cell]
            self.number_of_signals_per_frame = pd.merge(self.number_of_signals_per_frame, dataframe_series, on='time_in_seconds', how='left')
            pass

    def save_mean_amplitudes(self):
        with open(self.save_path + "Mean amplitudes of responding cells.txt", "a") as f:
            for mean_amplitude in self.general_mean_amplitude_list:
                filename = mean_amplitude[0]
                cell = '_cell_' + str(mean_amplitude[1])
                mean_amplitude_value = mean_amplitude[2]
                f.write(filename + cell + ": " + str(mean_amplitude_value) + " nM\n")

