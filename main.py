from postprocessing.postprocessing import BaseATPImageProcessor


if __name__ == '__main__':

    path = "Data/test.tif"
    parameters = {
        "wavelength_1": 1,
        "wavelength_2": 1
    }

    Processor = BaseATPImageProcessor(path, parameters)

    Processor.segment_cells()
    Processor.start_postprocessing()

    results = Processor.return_ratios()

