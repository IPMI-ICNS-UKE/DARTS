# from postprocessing.processing import ImageProcessor
# from postprocessing.postprocessing import ATPImageProcessor, plot_cells
# from stardist.models import StarDist2D
import time
import matplotlib.pyplot as plt
from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor


# def main():
if __name__ == '__main__':

    path_ATP = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_488-4-2-frame-duplicated-image.tif"
    # path_ATP_561 = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_561-4-2-frame-duplicated-image.tif"


    save_path_processed_ATP_images = "C:/Users/hueme/Desktop/testing/C-DARTS/Output/ATP/processed_ATP_images/"
    save_path_unprocessed_ATP_images = save_path_processed_ATP_images + "/raw_cell_images"

    path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/170424 2.tif"
    save_path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor = ImageProcessor(parameters)
    Processor.select_rois()
    Processor.start_postprocessing()
    Processor.save_image_files(save_path_processed_ATP_images)  # save processed cropped images
    fig = Processor.plot_rois()
    fig.savefig(save_path_processed_ATP_images + "rois.jpg")
