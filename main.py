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

    input_path = parameters["inputoutput"]["input_path"]

    if os.path.isdir(input_path):
        input_directory = input_path
        filename_list = os.listdir(input_path)
    else:
        input_directory = os.path.dirname(input_path)
        filename_list = [os.path.basename(input_path)]
    if parameters["properties"]["channel_format"] == "single":
        filename_list = [f for f in filename_list if fnmatch.fnmatch(f, '*_1.*')]# loop only over channel 1 files

    # definition of bead contacts for each file
    for file in filename_list:
        file_path = os.path.join(input_directory, file)
        bead_contact_gui = BeadContactGUI(file, file_path, info_saver.bead_contact_dict, parameters)
        bead_contact_gui.run_main_loop()
        del bead_contact_gui

    # save bead contacts on computer
    info_saver.save_bead_contact_information()

    files_with_bead_contact = [file for file in filename_list if info_saver.bead_contact_dict[file]]  # only files with cells that have a bead contact

    for file in files_with_bead_contact:
        list_of_bead_contacts = info_saver.bead_contact_dict[file]
        parameters["properties"]["list_of_bead_contacts"] = list_of_bead_contacts

        # find out end point
        latest_time_of_bead_contact = max([bead_contact.time_of_bead_contact for bead_contact in list_of_bead_contacts])
        end_frame_file = latest_time_of_bead_contact + parameters["properties"]["duration_of_measurement"] + 20  # not all frames need to be processed
        parameters["inputoutput"]["end_frame"] = end_frame_file

        parameters["inputoutput"]["filename"] = file
        filename = os.path.join(input_directory, file)
        Processor = ImageProcessor.fromfilename(filename, parameters, logger)

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
