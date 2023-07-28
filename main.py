from pathlib import Path
import tomli
import os
import json
import time
from stardist.models import StarDist2D
import argparse
from general.processing import ImageProcessor
from GUI import TDarts_GUI
from general.logger import Logger
from analysis.Bead_Contact_GUI import BeadContactGUI
import gc
from general.InfoToComputer import InfoToComputer

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

    model = StarDist2D.from_pretrained('2D_versatile_fluo')

    directory = parameters["inputoutput"]["path_to_input_combined"]
    filename_list = os.listdir(directory)
    filename_list = [file for file in filename_list if os.fsdecode(file).endswith(".tif")]

    # definition of bead contacts for each file
    for file in filename_list:
        file_path = parameters["inputoutput"]["path_to_input_combined"] + '/' + file
        bead_contact_gui = BeadContactGUI(file, file_path, info_saver.bead_contact_dict)
        bead_contact_gui.run_main_loop()
    del bead_contact_gui

    # save bead contacts on computer
    info_saver.save_bead_contact_information()

    files_with_bead_contact = [file for file in filename_list if info_saver.bead_contact_dict[file]]  # only files with cells that have a bead contact


    for file in files_with_bead_contact:
        parameters["properties"]["list_of_bead_contacts"] = info_saver.bead_contact_dict[file]
        filename = parameters["inputoutput"]["path_to_input_combined"] + '/' + file
        Processor = ImageProcessor.fromfilename(filename, parameters, logger)

        print("Now processing the following file: " + file)
        # Postprocessing pipeline
        Processor.start_postprocessing()

        # shape normalization
        normalized_cells_dict = Processor.apply_shape_normalization()

        # analysis: hotspot detection and dartboard projection
        number_of_analyzed_cells, number_of_analyzed_cells_with_hotspots, microdomains_timelines_dict = Processor.hotspot_detection(normalized_cells_dict)

        info_saver.number_of_analyzed_cells_in_total += number_of_analyzed_cells
        info_saver.number_of_analyzed_cells_with_hotspots_in_total += number_of_analyzed_cells_with_hotspots

        info_saver.add_signal_information(microdomains_timelines_dict)
        info_saver.general_mean_amplitude_list += Processor.give_mean_amplitude_list()

        average_dartboard_data_multiple_cells = Processor.dartboard(normalized_cells_dict)

        info_saver.dartboard_data_list.append(average_dartboard_data_multiple_cells)

        # save image files
        Processor.save_image_files()
        Processor.save_ratio_image_files()
        del Processor
        gc.collect()

    if files_with_bead_contact:  # if not empty
        # save number of signals per confocal sublayer/frame for all files and cells
        info_saver.save_number_of_signals()

        # save number of responding cells
        info_saver.save_number_of_responding_cells()

        # create a general dartboard for all analyzed cells
        info_saver.create_general_dartboard()

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
