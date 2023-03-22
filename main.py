from postprocessing.postprocessing import BaseCaImageProcessor


if __name__ == '__main__':

    path = "Data/170424 2_1.tif"
    parameters = {
        "wavelength_1": 1,
        "wavelength_2": 1
    }

    Processor = BaseCaImageProcessor(path, parameters)

    Processor.segment_cells()
    Processor.start_postprocessing()

    results = Processor.return_ratios()

