import logging
from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

import os
import skimage.io as io
from alive_progress import alive_bar
import time
import timeit
from stardist.models import StarDist2D

from GUI import TDarts_GUI
import argparse

# # instantiate logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
#
# # define handler and formatter
# handler = logging.StreamHandler()
# formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
#
# # add formatter to handler
# handler.setFormatter(formatter)
#
# # add handler to logger
# logger.addHandler(handler)

logging.basicConfig(filename="logfile",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logging.info("Running main.py")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
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

    # get the start time
    start_time = time.time()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    model = StarDist2D.from_pretrained('2D_versatile_fluo')

    Processor = ImageProcessor(parameters, model)
    Processor.start_postprocessing()

    savepath = parameters['inputoutput']['path_to_output'] + '/normalization/'
    os.makedirs(savepath, exist_ok=True)
    normalized_dartboard_data_multiple_cells = []

    print("\nProcessing now continues with: ")
    with alive_bar(len(Processor.cell_list), force_tty=True) as bar:
        for i, cell in enumerate(Processor.cell_list):
            time.sleep(.005)
            ratio = cell.give_ratio_image()
            try:
                sh_start = timeit.default_timer()
                normalized_ratio, centroid_coords_list = Processor.normalize_cell_shape(cell)
                sh_took = (timeit.default_timer() - sh_start) * 1000.0
                sh_sec, sh_min, sh_hour = convert_ms_to_smh(int(sh_took))
                print(f"Shape normalization of cell, {i + 1} "
                      f"took: {sh_hour:02d} h: {sh_min:02d} m: {sh_sec:02d} s :{int(sh_took):02d} ms")
            except Exception as E:
                print(E)
                print("Error in shape normalization")
                continue
            cell_image_radius_after_normalization = 50 # provisorisch...
            io.imsave(savepath+"cellratio"+str(i)+".tif", ratio)
            io.imsave(savepath+"cellratio_normalized"+str(i)+".tif", normalized_ratio)

            try:
                hd_start = timeit.default_timer()
                Processor.detect_hotspots(normalized_ratio, cell, i)
                hd_took = (timeit.default_timer() - hd_start) * 1000.0
                hd_sec, hd_min, hd_hour = convert_ms_to_smh(int(hd_took))
                print(f"Hotspot detection of cell, {i + 1} "
                      f"took: {hd_hour:02d} h: {hd_min:02d} m: {hd_sec:02d} s :{int(hd_took):02d} ms")
            except Exception as E:
                print(E)
                print("Error in Hotspot Detection")
                continue
            try:
                Processor.save_measurements()
            except Exception as E:
                print(E)
                print("Error in saving measurements")
                continue

            try:
                if(not cell.is_excluded):
                    db_start = timeit.default_timer()
                    if cell.bead_contact_site != 0:
                        average_dartboard_data_single_cell = Processor.generate_average_dartboard_data_single_cell(centroid_coords_list,
                                                                                                         cell,
                                                                                                         cell_image_radius_after_normalization,
                                                                                                         i)
                        normalized_dartboard_data_single_cell = Processor.normalize_average_dartboard_data_one_cell(average_dartboard_data_single_cell,
                                                                                                                  cell.bead_contact_site,
                                                                                                                  2)

                        normalized_dartboard_data_multiple_cells.append(normalized_dartboard_data_single_cell)
                    db_took = (timeit.default_timer() - db_start) * 1000.0
                    db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
                    print(f"Dartboard analysis of cell, {i + 1} "
                          f"took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms")
            except Exception as E:
                print(E)
                print("Error in Dartboard (single cell)")
                continue
            bar()

    try:
        db_start = timeit.default_timer()
        Processor.generate_average_and_save_dartboard_multiple_cells(normalized_dartboard_data_multiple_cells)
        db_took = (timeit.default_timer() - db_start) * 1000.0
        db_sec, db_min, db_hour = convert_ms_to_smh(int(db_took))
        print(f"\nDartboard plot: Done!"
              f" It took: {db_hour:02d} h: {db_min:02d} m: {db_sec:02d} s :{int(db_took):02d} ms")
    except Exception as E:
        print(E)
        print("Error in Dartboard (average dartboard for multiple cells)")

    Processor.save_image_files()  # save processed cropped images
    Processor.save_ratio_image_files()

    # get the end time
    end_time = time.time()
    # get the execution time
    elapsed_time = end_time - start_time
    print(f'\nExecution time: {float(elapsed_time):.1f}, seconds')

if __name__ == "__main__":
    logger.info("Program started")
    parser = argparse.ArgumentParser(description='Run program.')
    parser.add_argument('--no-gui', dest='gui', action='store_false',
                        help='run without graphical interface')
    parser.set_defaults(gui=False)

    args = parser.parse_args()

    main(args.gui)
    logger.info("Program finished")