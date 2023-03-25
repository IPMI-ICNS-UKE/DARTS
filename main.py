from postprocessing.postprocessing import BaseATPImageProcessor, plot_cells
from stardist.models import StarDist2D
import tensorflow as tf



if __name__ == '__main__':

    path = "/Users/dejan/Downloads/170424 2_1.tif"
    save_path = "/Users/dejan/Downloads/Test/"
    parameters = {
        "wavelength_1": 1,
        "wavelength_2": 1
    }
    segmentation_model = StarDist2D.from_pretrained('2D_versatile_fluo')
    Processor = BaseATPImageProcessor(path, parameters, segmentation_model)

    Processor.segment_cells()
    plot_cells(processor=Processor, path=save_path)

    Processor.start_postprocessing()
    #
    # results = Processor.return_ratios()