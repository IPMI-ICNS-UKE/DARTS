from postprocessing.postprocessing import BaseCaImageProcessor
from postprocessing.postprocessing import ATPImageProcessor, plot_cells
from stardist.models import StarDist2D
import matplotlib.pyplot as plt


if __name__ == '__main__':

    ATP = True

    parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }

    if ATP:
        path_wavelength_1 = "Data/230302_ATPOS_Beladung_100x_488-5.tif"
        path_wavelength_2 = "Data/230302_ATPOS_Beladung_100x_561-5.tif"

        save_path = "C:/Users/hueme/Desktop/testing/C-DARTS"

        # prints a list of available models
        StarDist2D.from_pretrained()
        segmentation_model = StarDist2D.from_pretrained('2D_versatile_fluo')
        Processor = ATPImageProcessor(path_wavelength_1, path_wavelength_2, segmentation_model, parameters)

        Processor.segment_cells()
        Processor.start_postprocessing()
        Processor.save_image_files(save_path)


    else:
        path = "Data/170424 2_1.tif"
        segmentation_model = StarDist2D.from_pretrained('2D_versatile_fluo')
        Processor = BaseCaImageProcessor(path, parameters, segmentation_model)

        Processor.segment_cells()
        # plot_cells(processor=Processor, path=save_path)

        # Processor.start_postprocessing()
        #
        # results = Processor.return_ratios()




