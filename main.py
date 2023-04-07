from postprocessing.processing import ImageProcessor
import matplotlib.pyplot as plt

if __name__ == '__main__':

    path = "Data/170424 JMP HN1L-KO Beads/170424 HN1L K2 OKT3 Beads/170424 2.tif"
    save_path = ""
    parameters = {
        "wavelength_1": 1,
        "wavelength_2": 1
    }
    Processor = ImageProcessor(path, parameters)

    Processor.select_rois()
    fig = Processor.plot_rois()
    fig.savefig(save_path+"rois.jpg")



#    Processor.start_postprocessing()
    #
    # results = Processor.return_ratios()