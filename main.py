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
    for i, cell in enumerate(Processor.cell_list):
        ratio = cell.give_ratio_image()
        normalized_ratio, centroid_coords_list = Processor.normalize_cell_shape(cell)
        cell_image_radius_after_normalization = 50 # provisorisch...
        io.imsave(savepath+"cellratio"+str(i)+".tif", ratio)
        io.imsave(savepath+"cellratio_normalized"+str(i)+".tif", normalized_ratio)

        Processor.detect_hotspots(normalized_ratio, cell, i)
        Processor.save_measurements()
        Processor.dartboard_projection(centroid_coords_list, cell, cell_image_radius_after_normalization, i)

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