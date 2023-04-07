
from postprocessing.processing import ImageProcessor
from postprocessing.postprocessing import ATPImageProcessor, plot_cells
import matplotlib.pyplot as plt

if __name__ == '__main__':

  ATP=false
  
   parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }

  if ATP:
    path = "/Users/dejan/Downloads/MemBrite-Fix-488-568-640-yeast-mix.jpg"
    save_path = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"
    Processor = ATPImageProcessor(path, parameters)

    Processor.segment_cells()
    Processor.start_postprocessing()
   else:
    path = "Data/170424 JMP HN1L-KO Beads/170424 HN1L K2 OKT3 Beads/170424 2.tif"
    save_path = ""
    Processor = ImageProcessor(path, parameters)

    Processor.select_rois()
    fig = Processor.plot_rois()
    fig.savefig(save_path+"rois.jpg")