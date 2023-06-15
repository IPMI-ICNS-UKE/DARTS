from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

import os
import skimage.io as io

from GUI import TDarts_GUI
import argparse


def main(gui_enabled):
    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor = ImageProcessor(parameters)
    Processor.start_postprocessing()

    savepath = parameters['inputoutput']['path_to_output'] + '/normalization/'
    os.makedirs(savepath, exist_ok=True)
    dartboard_data_multiple_cells = []

    for i, cell in enumerate(Processor.cell_list):
        ratio = cell.give_ratio_image()
        try:
            normalized_ratio, centroid_coords_list = Processor.normalize_cell_shape(cell)
        except Exception as E:
            print(E)
            print("Error in shape normalization")
            continue
        cell_image_radius_after_normalization = 50 # provisorisch...
        io.imsave(savepath+"cellratio"+str(i)+".tif", ratio)
        io.imsave(savepath+"cellratio_normalized"+str(i)+".tif", normalized_ratio)

        try:
            Processor.detect_hotspots(normalized_ratio, cell, i)
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
                dartboard_data_single_cell = Processor.generate_average_dartboard_data_single_cell(centroid_coords_list, cell, cell_image_radius_after_normalization, i)

                dartboard_data_multiple_cells.append(dartboard_data_single_cell)
        except Exception as E:
            print(E)
            print("Error in Dartboard (single cell)")
            continue

    try:
        Processor.generate_average_and_save_dartboard_multiple_cells(dartboard_data_multiple_cells)
    except Exception as E:
        print(E)
        print("Error in Dartboard (average dartboard for multiple cells)")

    Processor.save_image_files()  # save processed cropped images
    Processor.save_ratio_image_files()
    # fig = Processor.plot_rois()
    # fig.savefig(save_path_Ca_cAMP + "rois.jpg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run program.')
    parser.add_argument('--no-gui', dest='gui', action='store_false',
                        help='run without graphical interface')
    parser.set_defaults(gui=True)

    args = parser.parse_args()

    main(args.gui)

