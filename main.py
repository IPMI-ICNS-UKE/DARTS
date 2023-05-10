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

    save_path_Ca_cAMP = "C:/Users/hueme/Desktop/testing/C-DARTS/Output/Ca_cAMP"

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor = ImageProcessor(parameters)
    # Processor.select_rois()
    Processor.start_postprocessing()
    Processor.save_image_files(save_path_Ca_cAMP)  # save processed cropped images
    Processor.save_ratio_image_files(save_path_Ca_cAMP)
    # fig = Processor.plot_rois()
    # fig.savefig(save_path_processed_ATP_images + "rois.jpg")
    # fig.savefig(save_path_Ca_cAMP + "rois.jpg")
