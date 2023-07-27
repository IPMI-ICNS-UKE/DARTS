from pathlib import Path
import tomli
import os
import json
import time
from stardist.models import StarDist2D
import argparse
import skimage.io as io
from general.processing import ImageProcessor
from GUI import TDarts_GUI
from general.logger import Logger
from analysis.Bead_Contact_GUI import BeadContactGUI
from analysis.MeanDartboard import MeanDartboardGenerator
import pandas as pd
import numpy as np
import gc

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logger = Logger()

def save_bead_contact_information(save_path, bead_contact_dict):
    with open(save_path + 'Bead_contact_information.txt', 'w') as f:
        for file in bead_contact_dict:
            f.write("Filename: " + file + "\n")
            for bead_contact in bead_contact_dict[file]:
                f.write(" Bead contact: " + bead_contact.to_string() + "\n")
            f.write("\n")

def save_number_of_responding_cells(save_path, number_of_analyzed_cells_in_total, number_of_analyzed_cells_with_hotspots_in_total):
    with open(save_path + 'Number of responding cells.txt', 'w') as f:
        f.write("Number of analyzed cells in total: " + str(number_of_analyzed_cells_in_total) + "\n")
        f.write("Number of analyzed cells with hotspots in total: " + str(number_of_analyzed_cells_with_hotspots_in_total) + "\n")
        if number_of_analyzed_cells_in_total != 0:
            percentage_of_responding_cells = float(
                number_of_analyzed_cells_with_hotspots_in_total) / number_of_analyzed_cells_in_total * 100
        else:
            percentage_of_responding_cells = 0
        f.write("Percentage of responding cells: " + str(percentage_of_responding_cells) + "%")

def create_general_dartboard(save_path, number_of_analyzed_cells, frame_rate, experiment_name, dartboard_sections, dartboard_areas_per_section):
    source_path = save_path + 'Dartboard_data_all_files'
    measurement_name = "dartboard_for_all_analyzed_cells"

    mean_dartboard_generator = MeanDartboardGenerator(source_path, save_path, number_of_analyzed_cells, frame_rate, experiment_name, measurement_name, dartboard_sections, dartboard_areas_per_section)
    mean_dartboard_generator.calculate_dartboard_data_for_all_cells()

def save_number_of_signals(save_path, excel_filename_general, number_of_signals_per_frame):
    with pd.ExcelWriter(save_path + excel_filename_general) as writer:
        sheet_name = "Number of signals in each frame"
        number_of_signals_per_frame.to_excel(writer, sheet_name=sheet_name, index=False)

def save_mean_amplitudes(save_path, mean_amplitude_list):
    with open(save_path + "Mean amplitudes of responding cells.txt", "a") as f:
        for mean_amplitude in mean_amplitude_list:
            f.write(str(mean_amplitude) + " nM\n")

def main(gui_enabled):
    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()
    del gui

    start_time = time.time()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    directory = parameters["inputoutput"]["path_to_input_combined"]
    filename_list = os.listdir(directory)

    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    model = StarDist2D.from_pretrained('2D_versatile_fluo')
    dartboard_data_list = []

    filename_list = [file for file in filename_list if os.fsdecode(file).endswith(".tif")]

    # definition of bead contacts for each file
    bead_contact_dict = {}
    for file in filename_list:
        file_path = parameters["inputoutput"]["path_to_input_combined"] + '/' + file
        image = io.imread(file_path)
        bead_contact_gui = BeadContactGUI(file, image, bead_contact_dict)
        bead_contact_gui.run_main_loop()
    del bead_contact_gui
    del image

    # save bead contacts on computer
    save_path = parameters["inputoutput"]["path_to_output"] + '/'
    save_bead_contact_information(save_path, bead_contact_dict)

    number_of_analyzed_cells_in_total = 0
    number_of_analyzed_cells_with_hotspots_in_total = 0
    general_mean_amplitude_list = []

    number_of_signals_per_frame = pd.DataFrame()
    frames_per_second = parameters["properties"]["frames_per_second"]
    duration_of_measurement_in_frames = int(16 * frames_per_second)  # from 1s before bead contact to 15s after bead contact
    list_of_time_points = []
    for frame in range(duration_of_measurement_in_frames):
        time_point = (frame - frames_per_second)/frames_per_second
        list_of_time_points.append(time_point)

    number_of_signals_per_frame['time_in_seconds'] = list_of_time_points
    files_with_bead_contact = [file for file in filename_list if bead_contact_dict[file]]

    for file in files_with_bead_contact:
        list_of_bead_contacts_for_file = bead_contact_dict[file]

        Processor = ImageProcessor(file, list_of_bead_contacts_for_file, parameters, model, logger)
        print("Now processing the following file: " + file)
        # Postprocessing pipeline
        Processor.start_postprocessing()

        # assignment of bead contacts to the cells
        Processor.assign_bead_contacts_to_cells()

        # shape normalization
        normalized_cells_dict = Processor.apply_shape_normalization()

        # analysis: hotspot detection and dartboard projection
        number_of_analyzed_cells, number_of_analyzed_cells_with_hotspots, microdomains_timelines_dict = Processor.hotspot_detection(normalized_cells_dict)
        number_of_analyzed_cells_in_total += number_of_analyzed_cells
        number_of_analyzed_cells_with_hotspots_in_total += number_of_analyzed_cells_with_hotspots
        for filename_cell in microdomains_timelines_dict:
            filename = filename_cell[0]
            cell_index = filename_cell[1]
            title_of_microdomains_timeline = filename + "_cell_" + str(cell_index)

            dataframe_series = microdomains_timelines_dict[filename_cell]
            number_of_signals_per_frame[title_of_microdomains_timeline] = dataframe_series[title_of_microdomains_timeline].tolist()

        general_mean_amplitude_list = general_mean_amplitude_list + Processor.give_mean_amplitude_list()

        average_dartboard_data_multiple_cells = Processor.dartboard(normalized_cells_dict)

        dartboard_data_list.append(average_dartboard_data_multiple_cells)

        # save files
        Processor.save_image_files()
        Processor.save_ratio_image_files()
        del Processor
        gc.collect()


    # save number of signals per confocal sublayer/frame for all files and cells
    excel_filename_general = parameters["inputoutput"]["excel_filename_all_cells"]
    save_number_of_signals(save_path, excel_filename_general, number_of_signals_per_frame)

    # save number of responding cells
    save_number_of_responding_cells(save_path, number_of_analyzed_cells_in_total,
                                    number_of_analyzed_cells_with_hotspots_in_total)

    #create a general dartboard for all analyzed cells
    create_general_dartboard(save_path,
                             number_of_analyzed_cells_in_total,
                             parameters["properties"]["frames_per_second"],
                             parameters["inputoutput"]["experiment_name"],
                             parameters["properties"]["dartboard_number_of_sections"],
                             parameters["properties"]["dartboard_number_of_areas_per_section"])

    save_mean_amplitudes(save_path, general_mean_amplitude_list)

    end_time = time.time()
    # execution time
    elapsed_time = end_time - start_time
    print("\n")
    logger.log_and_print(message=f'Execution time: {float(elapsed_time):.1f}, seconds',
                  level=logger.logging.INFO, logger=logger)


if __name__ == "__main__":

    logger.info("Program started")
    parser = argparse.ArgumentParser(description='Run program.')
    parser.add_argument('--no-gui', dest='gui', action='store_false',
                        help='run without graphical interface')
    parser.set_defaults(gui=True)

    args = parser.parse_args()

    main(args.gui)
    logger.info("Program finished")
    quit()
