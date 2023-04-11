from postprocessing.postprocessing import ATPImageProcessor, plot_cells

if __name__ == '__main__':
    path_wavelength_1 = "/Users/dejan/Documents/GitHub/T-DARTS/230302_ATPOS_Beladung_100x_488-5.tif"
    path_wavelength_2 = "/Users/dejan/Documents/GitHub/T-DARTS/230302_ATPOS_Beladung_100x_561-5.tif"

    save_path = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"
    parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }

    Processor = ATPImageProcessor(path_wavelength_1, path_wavelength_2, parameters)

    Processor.segment_cells()
    Processor.start_postprocessing()
    Processor.save_image_files(save_path)

    # results = Processor.return_ratios()

