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
from analysis.Dartboard import DartboardGenerator


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logger = Logger()


def main(gui_enabled):
    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()

    start_time = time.time()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    directory = parameters["inputoutput"]["path_to_input_combined"]
    filename_list = os.listdir(directory)

    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    model = StarDist2D.from_pretrained('2D_versatile_fluo')
    dartboard_data_list = []
    number_of_cells_with_dartboard = 0

    filename_list = [file for file in filename_list if os.fsdecode(file).endswith(".tif")]

    for file in filename_list:
        Processor = ImageProcessor(file, parameters, model, logger)

        # Postprocessing pipeline
        Processor.start_postprocessing()

        # shape normalization
        normalized_cells_dict = Processor.apply_shape_normalization()

        # analysis: hotspot detection and dartboard projection
        Processor.hotspot_detection(normalized_cells_dict)
        average_dartboard_data_multiple_cells, number_of_cells = Processor.dartboard(normalized_cells_dict)
        number_of_cells_with_dartboard += number_of_cells
        dartboard_data_list.append(average_dartboard_data_multiple_cells)

        # save files
        Processor.save_image_files()
        Processor.save_ratio_image_files()


    # create mean dartboard plot for multiple files/cells
    save_path = parameters["inputoutput"]["path_to_output"]
    frame_rate = parameters["properties"]["frames_per_second"]
    experiment_name = parameters["properties"]["experiment_name"]
    measurement_name = parameters["properties"]["day_of_measurement"] + '_' + experiment_name
    results_folder = save_path
    dartboard_number_of_sections = parameters["properties"]["dartboard_number_of_sections"]
    dartboard_number_of_areas_per_section = parameters["properties"]["dartboard_number_of_areas_per_section"]
    dartboard_generator = DartboardGenerator(save_path, frame_rate, measurement_name, experiment_name, results_folder)
    average_dartboard_data_all_measurements = dartboard_generator.calculate_mean_dartboard_multiple_cells(number_of_cells_with_dartboard,
                                                                                                          dartboard_data_list,
                                                                                                          dartboard_number_of_sections,
                                                                                                          dartboard_number_of_areas_per_section)
    dartboard_generator.save_dartboard_plot(average_dartboard_data_all_measurements, number_of_cells_with_dartboard, dartboard_number_of_sections, dartboard_number_of_areas_per_section)


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
