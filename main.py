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
        path_wavelength_1 = "Data/230221_ATPOS_Optimierung_1_w1Dual-CF-488-561-camera2-0001.tif"
        path_wavelength_2 = "Data/230221_ATPOS_Optimierung_1_w2Dual-CF-561-488-camera1-0001.tif"

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




