
from postprocessing.processing import ImageProcessor


parameters = 0

if __name__ == '__main__':

    parameters = {
        "wavelength_1": 488,
        "wavelength_2": 561
    }
    ATP_flag = False

    path_ATP = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_488-4-2-frame-duplicated-image.tif"
    # path_ATP_561 = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230302_ATPOS_Beladung_100x_561-4-2-frame-duplicated-image.tif"

    save_path_processed_ATP_images = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"
    save_path_unprocessed_ATP_images = save_path_processed_ATP_images + "/raw_cell_images"

    path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/170424 2.tif"
    save_path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"

    Processor = ImageProcessor(path_Ca_cAMP, parameters, ATP_flag)
    # Processor.save_image_files(save_path_unprocessed_ATP_images)  # save unprocessed cropped images
    Processor.start_postprocessing()
    Processor.save_image_files(save_path_Ca_cAMP)  # save processed cropped images

    fig = Processor.plot_rois()
    fig.savefig(save_path_processed_ATP_images + "rois.jpg")
