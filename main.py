from pathlib import Path
import tomli
import os
import json
import time
import argparse
from general.processing import ImageProcessor
from GUI import TDarts_GUI
from general.logger import Logger
from analysis.Bead_Contact_GUI import BeadContactGUI
import gc
from general.InfoToComputer import InfoToComputer
import glob

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logger = Logger()


def main(gui_enabled):
    start_time = time.time()

    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()
        del gui

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    info_saver = InfoToComputer(parameters)

    if parameters["input_output"]["image_conf"] == "two-in-one":
        directory = parameters["input_output"]["path_to_input_combined"]
    elif parameters["input_output"]["image_conf"] == "single":
        directory = parameters["input_output"]["path_to_input_1"]
    filename_list = os.listdir(directory)
    filename_list = [file for file in filename_list if os.fsdecode(file).endswith(".tif")]
    if parameters["input_output"]["image_conf"] == "single":
        filename_list = [os.path.basename(file) for file in glob.glob(directory + "/*1.tif")]# loop only over channel 1 files

    # definition of bead contacts for each file
    for file in filename_list:
        file_path = directory + '/' + file
        bead_contact_gui = BeadContactGUI(file, file_path, info_saver.bead_contact_dict, parameters)
        bead_contact_gui.run_main_loop()
        del bead_contact_gui

    # save bead contacts on computer
    info_saver.save_bead_contact_information()

    files_with_bead_contact = [file for file in filename_list if info_saver.bead_contact_dict[file]]  # only files with cells that have a bead contact


    for file in files_with_bead_contact:
        list_of_bead_contacts = info_saver.bead_contact_dict[file]
        parameters["properties_of_measurement"]["list_of_bead_contacts"] = list_of_bead_contacts

        # find out end point
        latest_time_of_bead_contact = max([bead_contact.time_of_bead_contact for bead_contact in list_of_bead_contacts])
        end_frame_file = latest_time_of_bead_contact + parameters["properties_of_measurement"]["duration_of_measurement"] + 20  # not all frames need to be processed
        parameters["input_output"]["end_frame"] = end_frame_file

        # find out filename
        if parameters["input_output"]["image_conf"] == "two-in-one":
            filename = parameters["input_output"]["path_to_input_combined"] + '/' + file
            parameters["input_output"]["filename"] = file
            Processor = ImageProcessor.fromfilename_split(filename, parameters, logger)
        elif parameters["input_output"]["image_conf"] == "single":
            filename_ch1 = parameters["input_output"]["path_to_input_1"] + '/' + file
            filename_ch2 = parameters["input_output"]["path_to_input_1"] + '/' + file.replace("1.tif", "2.tif")
            parameters["input_output"]["filename"] = file
            Processor = ImageProcessor.fromfilename_combine(filename_ch1, filename_ch2, parameters, logger)


        print("Now processing the following file: " + file)
        # Postprocessing pipeline
        Processor.start_postprocessing()

        # shape normalization
        normalized_cells_dict = Processor.apply_shape_normalization()

        # analysis: hotspot detection and dartboard projection
        number_of_analyzed_cells, number_of_responding_cells, microdomains_timelines_dict = Processor.hotspot_detection(normalized_cells_dict)

        info_saver.number_of_analyzed_cells_in_total += number_of_analyzed_cells
        info_saver.number_of_responding_cells_in_total += number_of_responding_cells

        info_saver.add_signal_information(microdomains_timelines_dict)
        info_saver.general_mean_amplitude_list += Processor.give_mean_amplitude_list()

        Processor.dartboard(normalized_cells_dict, info_saver)


        # save image files
        # Processor.save_image_files()
        # Processor.save_ratio_image_files()
        del Processor
        gc.collect()

    if files_with_bead_contact:  # if not empty
        # save number of signals per confocal sublayer/frame for all files and cells
        info_saver.save_number_of_signals()

        # save number of responding cells
        info_saver.save_number_of_responding_cells()

        # save mean amplitudes to the computer
        info_saver.save_mean_amplitudes()


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
