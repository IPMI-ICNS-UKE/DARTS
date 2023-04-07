from postprocessing.postprocessing import ATPImageProcessor, plot_cells

if __name__ == '__main__':

    path = "/Users/dejan/Downloads/MemBrite-Fix-488-568-640-yeast-mix.jpg"
    save_path = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"
    parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }

    Processor = ATPImageProcessor(path, parameters)

    Processor.segment_cells()
    Processor.start_postprocessing()

    # results = Processor.return_ratios()