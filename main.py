from pathlib import Path
import tomli
import os
import json
import time
import argparse
from src.general.processing import ImageProcessor
from GUI import TDarts_GUI
from src.general.logger import Logger
from src.analysis.Bead_Contact_GUI import BeadContactGUI
from src.analysis.GUI_no_beads import GUInoBeads
import gc
from src.general.InfoToComputer import InfoToComputer
import fnmatch
try:
    import javabridge
    import bioformats
    bf_avail = True
except Exception as E:
    print(E)
    print("continuing without bioformats library")
    bf_avail = False

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logger = Logger()


def main(gui_enabled):
    start_time = time.time()

    if bf_avail:
        max_heap_size = "512M"
        javabridge.start_vm(class_path=bioformats.JARS, run_headless=True, max_heap_size=max_heap_size)
        # suppress bioformats warnings/ debug messages
        myloglevel = "ERROR"
        rootLoggerName = javabridge.get_static_field("org/slf4j/Logger", "ROOT_LOGGER_NAME", "Ljava/lang/String;")
        rootLogger = javabridge.static_call("org/slf4j/LoggerFactory", "getLogger",
                                            "(Ljava/lang/String;)Lorg/slf4j/Logger;", rootLoggerName)
        logLevel = javabridge.get_static_field("ch/qos/logback/classic/Level", myloglevel,
                                               "Lch/qos/logback/classic/Level;")
        javabridge.call(rootLogger, "setLevel", "(Lch/qos/logback/classic/Level;)V", logLevel)

    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()
        del gui

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    info_saver = InfoToComputer(parameters)

    input_path = parameters["input_output"]["path"]

    if os.path.isdir(input_path):
        input_directory = input_path
    else:
        input_directory = os.path.dirname(input_path)
    files_for_further_processing = os.listdir(input_directory)
    files_for_further_processing = [file for file in files_for_further_processing if not file.startswith(".")]  # exclude hidden files..

    if parameters["input_output"]["image_conf"] == "single":
        files_for_further_processing = [f for f in files_for_further_processing if fnmatch.fnmatch(f, '*_1.*')]  # loop only over channel 1 files

    if parameters["properties_of_measurement"]["bead_contact"]:  # if bead contacts are defined
        # definition of bead contacts for each file
        for file in files_for_further_processing:
            file_path = os.path.join(input_directory, file)
            bead_contact_gui = BeadContactGUI(file, file_path, info_saver.bead_contact_dict, parameters)
            bead_contact_gui.run_main_loop()
            del bead_contact_gui

        # save bead contacts on computer
        info_saver.save_bead_contact_information()
        files_for_further_processing = [file for file in files_for_further_processing if info_saver.bead_contact_dict[file]]  # only files with cells that have a bead contact
    else:  # no bead contacts
        if parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
            time_of_addition_dict = dict()
            for file in files_for_further_processing:
                file_path = os.path.join(input_directory, file)
                gui_no_beads = GUInoBeads(file, file_path, parameters)
                gui_no_beads.run_main_loop()
                time_of_addition_dict[file] = gui_no_beads.get_time_of_addition()
                del gui_no_beads
        elif parameters["properties_of_measurement"]["imaging_local_or_global"] == 'local':
            pass

    for file in files_for_further_processing:
        if parameters["properties_of_measurement"]["bead_contact"]:
            list_of_bead_contacts = info_saver.bead_contact_dict[file]
            parameters["properties_of_measurement"]["list_of_bead_contacts"] = list_of_bead_contacts

            # find out end point
            latest_time_of_bead_contact = max([bead_contact.time_of_bead_contact for bead_contact in list_of_bead_contacts])
            end_frame_file = int(latest_time_of_bead_contact + parameters["properties_of_measurement"]["duration_of_measurement"])
            parameters["input_output"]["end_frame"] = end_frame_file
            time_of_addition = None
        else:
            parameters["input_output"]["end_frame"] = None
            if parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
                time_of_addition = time_of_addition_dict[file]
            else:
                time_of_addition = None

        parameters["input_output"]["filename"] = file
        filename = os.path.join(input_directory, file)
        Processor = ImageProcessor.fromfilename(filename, parameters, logger, time_of_addition)


        print("Now processing the following file: " + file)
        # Postprocessing pipeline
        Processor.start_postprocessing()

        # shape normalization
        if parameters["processing_pipeline"]["shape_normalization"]["shape_normalization"]:
            cells_dict = Processor.apply_shape_normalization()  # cells_dict[cell] = (normalized_ratio, mean_ratio_value_list, radii_after_normalization, centroid_coords_list)
        else:
            cells_dict = Processor.generate_cell_dict_without_shape_normalization()

        if parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
            # save global measurement data (mean ratio values for each cell)
            Processor.global_measurement(info_saver)

        # analysis: hotspot detection and dartboard projection
        if parameters["processing_pipeline"]["analysis"]["hotspot_detection"]:  # if hotspot detection in pipeline

            number_of_analyzed_cells, number_of_responding_cells, microdomains_timelines_dict = Processor.hotspot_detection(cells_dict)

            info_saver.number_of_analyzed_cells_in_total += number_of_analyzed_cells
            info_saver.number_of_responding_cells_in_total += number_of_responding_cells

            info_saver.add_signal_information(microdomains_timelines_dict)
            info_saver.general_mean_amplitude_list += Processor.give_mean_amplitude_list()

        if parameters["processing_pipeline"]["analysis"]["dartboard_projection"]:  # if dartboard projection in pipeline; only possible if shape normlization in pipeline
            Processor.dartboard(cells_dict, info_saver)

        del Processor
        gc.collect()

    if files_for_further_processing:  # if not empty
        if parameters["processing_pipeline"]["analysis"]["hotspot_detection"]:  # if hotspot detection in pipeline
            # save number of signals per confocal sublayer/frame for all files and cells
            info_saver.save_number_of_signals()

            # save number of responding cells
            info_saver.save_number_of_responding_cells()

            # save mean amplitudes to the computer
            info_saver.save_mean_amplitudes()
        if parameters["properties_of_measurement"]["imaging_local_or_global"] == 'global':
            info_saver.save_global_data()


    end_time = time.time()
    # execution time
    elapsed_time = end_time - start_time
    print("\n")
    logger.log_and_print(message=f'Execution time: {float(elapsed_time):.1f}, seconds',
                  level=logger.logging.INFO, logger=logger)
    if bf_avail:
        javabridge.kill_vm()

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
