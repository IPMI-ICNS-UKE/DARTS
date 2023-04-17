
#from postprocessing.processing import ImageProcessor
#from postprocessing.postprocessing import ATPImageProcessor, plot_cells

#from stardist.models import StarDist2D
import time

import matplotlib.pyplot as plt


from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

def main():
    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor  = ImageProcessor(parameters)
    Processor.select_rois()
    #Processor.plot_rois()

if __name__ == '__main__':
    main()