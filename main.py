from postprocessing.processing import ImageProcessor

if __name__ == '__main__':

    path = "/Users/dejan/Downloads/170424 2_1.tif"
    save_path = "/Users/dejan/Downloads/Test/"
    parameters = {
        "wavelength_1": 1,
        "wavelength_2": 1
    }
    Processor = ImageProcessor(path, parameters)

    Processor.select_rois()

#    Processor.start_postprocessing()
    #
    # results = Processor.return_ratios()