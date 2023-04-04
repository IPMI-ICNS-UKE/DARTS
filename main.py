from postprocessing.postprocessing import ATPImageProcessor, plot_cells



if __name__ == '__main__':

    path = "/Users/dejan/Downloads/170424 2_1.tif"
    save_path = "/Users/dejan/Downloads/Test/"
    parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }

    Processor = ATPImageProcessor(path, parameters)

    Processor.segment_cells()

    Processor.start_postprocessing()

    # results = Processor.return_ratios()