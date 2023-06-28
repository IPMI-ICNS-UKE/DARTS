import logging
from pathlib import Path
import tomli
import os
import json
import skimage.io as io
from alive_progress import alive_bar
import time
import timeit
from stardist.models import StarDist2D
import argparse

from postprocessing.processing import ImageProcessor
from GUI import TDarts_GUI


def log_and_print(message: str, level, logger: logging.Logger):
    logger.log(level=level, msg=message)  # log as normal
    print(message)  # prints to stdout by default


logging.basicConfig(filename="logfile",
                    filemode='w',
                    format='%(asctime)s-%(levelname)s-%(message)s',
                    datefmt='%Y:%m:%d %H:%M:%S',
                    level=logging.INFO,
                    )

logger = logging.getLogger(__name__)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def convert_ms_to_smh(millis):
    seconds = int(millis / 1000) % 60
    minutes = int(millis / (1000 * 60)) % 60
    hours = int(millis / (1000 * 60 * 60)) % 24
    return seconds, minutes, hours


def main(gui_enabled):
    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()

    start_time = time.time()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    model = StarDist2D.from_pretrained('2D_versatile_fluo')

    Processor = ImageProcessor(parameters, model)
    Processor.start_postprocessing()

    savepath = parameters['inputoutput']['path_to_output'] + '/normalization/'
    os.makedirs(savepath, exist_ok=True)

    normalized_dartboard_data_per_second_multiple_cells = []

    print("\n")
    log_and_print(message="Processing now continues with: ", level=logging.INFO, logger=logger)
    with alive_bar(len(Processor.cell_list), force_tty=True) as bar:
        for i, cell in enumerate(Processor.cell_list):
            time.sleep(.005)
            ratio = cell.give_ratio_image()
            try:
                sh_start = timeit.default_timer()
                normalized_ratio, centroid_coords_list = Processor.normalize_cell_shape(cell)
                mean_ratio_value_list, radii_after_normalization = Processor.extract_information_for_hotspot_detection(normalized_ratio)

                sh_took = (timeit.default_timer() - sh_start) * 1000.0
                sh_sec, sh_min, sh_hour = convert_ms_to_smh(int(sh_took))
                log_and_print(message=f"Shape normalization of cell {i + 1} "
                                      f"took: {sh_hour:02d} h: {sh_min:02d} m: {sh_sec:02d} s :{int(sh_took):02d} ms",
                              level=logging.INFO, logger=logger)
            except Exception as E:
                print(E)
                log_and_print(message="Exception occurred: Error in shape normalization",
                              level=logging.ERROR, logger=logger)
                continue

            io.imsave(savepath+"cellratio"+str(i)+".tif", ratio)
            io.imsave(savepath+"cellratio_normalized"+str(i)+".tif", normalized_ratio)


            try:
                hd_start = timeit.default_timer()
                Processor.detect_hotspots(normalized_ratio, mean_ratio_value_list, cell, i)
                hd_took = (timeit.default_timer() - hd_start) * 1000.0
                hd_sec, hd_min, hd_hour = convert_ms_to_smh(int(hd_took))
                log_and_print(message=f"Hotspot detection of cell {i + 1} "
                                      f"took: {hd_hour:02d} h: {hd_min:02d} m: {hd_sec:02d} s :{int(hd_took):02d} ms",
                              level=logging.INFO, logger=logger)
            except Exception as E:
                print(E)
                log_and_print(message="Exception occurred: Error in Hotspot Detection !",
                              level=logging.ERROR, logger=logger)
                continue

            try:
                Processor.save_measurements(i)
            except Exception as E:
                print(E)
                log_and_print(message="Exception occurred: Error in saving measurements",
                              level=logging.ERROR, logger=logger)
                continue

            try:
                if(True or not cell.is_excluded):  # maybe delete cell.is_excluded statement...

                    db_start = timeit.default_timer()
                    if cell.bead_contact_site != 0:
                        average_dartboard_data_per_second_single_cell = Processor.generate_average_dartboard_data_per_second_single_cell(centroid_coords_list,
                                                                                                         cell,
                                                                                                         radii_after_normalization,
                                                                                                         i)
                        normalized_dartboard_data_per_second_single_cell = Processor.normalize_average_dartboard_data_one_cell(average_dartboard_data_per_second_single_cell,
                                                                                                                  cell.bead_contact_site,
                                                                                                                  2)


                        normalized_dartboard_data_per_second_multiple_cells.append(normalized_dartboard_data_per_second_single_cell)

                    db_took = (timeit.default_timer() - db_start) * 1000.0
                    db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
                    log_and_print(message=f"Dartboard analysis of cell {i + 1} "
                                          f"took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms",
                                  level=logging.INFO, logger=logger)
                else:
                    log_and_print(message=f"No Dartboard analysis of cell {i + 1} ",
                                  level=logging.WARNING, logger=logger)
            except Exception as E:
                print(E)
                log_and_print(message="Exception occurred: Error in Dartboard (single cell)",
                              level=logging.ERROR, logger=logger)
                continue
            bar()

    try:
        db_start = timeit.default_timer()
        Processor.generate_average_and_save_dartboard_multiple_cells(normalized_dartboard_data_per_second_multiple_cells)
        db_took = (timeit.default_timer() - db_start) * 1000.0
        db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
        print("\n")
        log_and_print(message=f"Dartboard plot: Done!"
                              f" It took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms",
                      level=logging.INFO, logger=logger)
    except Exception as E:
        print(E)
        log_and_print(message="Error in Dartboard (average dartboard for multiple cells)",
                      level=logging.ERROR, logger=logger)

    Processor.save_image_files()  # save processed cropped images
    Processor.save_ratio_image_files()

    end_time = time.time()
    # execution time
    elapsed_time = end_time - start_time
    print("\n")
    log_and_print(message=f'Execution time: {float(elapsed_time):.1f}, seconds',
                  level=logging.INFO, logger=logger)


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
