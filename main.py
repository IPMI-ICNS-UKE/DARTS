from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

import os
import skimage.io as io

from GUI import TDarts_GUI


# def main():
if __name__ == '__main__':

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    gui = TDarts_GUI()
    gui.run_main_loop()

    Processor = ImageProcessor(parameters)
    Processor.start_postprocessing()

    savepath = parameters['inputoutput']['path_to_output'] + '/normalization/'
    os.makedirs(savepath, exist_ok=True)
    for i, cell in enumerate(Processor.cell_list):
        ratio = cell.calculate_ratio_image()
        normalized_ratio = Processor.normalize_cell_shape(cell)
        io.imsave(savepath+"cellratio"+str(i)+".tif", ratio)
        io.imsave(savepath+"cellratio_normalized"+str(i)+".tif", normalized_ratio)


    Processor.save_image_files()  # save processed cropped images
    Processor.save_ratio_image_files()
    # fig = Processor.plot_rois()
    # fig.savefig(save_path_Ca_cAMP + "rois.jpg")