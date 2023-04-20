

#from postprocessing.processing import ImageProcessor
#from postprocessing.postprocessing import ATPImageProcessor, plot_cells
#from stardist.models import StarDist2D
import time
import matplotlib.pyplot as plt
from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

# def main():
if __name__ == '__main__':

    save_path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor = ImageProcessor(parameters)
    Processor.select_rois()
    Processor.start_postprocessing()
    Processor.save_image_files(save_path_Ca_cAMP)  # save processed cropped images
    fig = Processor.plot_rois()
    fig.savefig(save_path_Ca_cAMP + "rois.jpg")