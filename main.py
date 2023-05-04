from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor

# def main():
if __name__ == '__main__':

    save_path_Ca_cAMP = "/Users/dejan/Documents/Doktorarbeit/Python_save_path"

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor = ImageProcessor(parameters)
    Processor.start_postprocessing()
    Processor.save_image_files(save_path_Ca_cAMP)  # save processed cropped images
    Processor.save_ratio_image_files(save_path_Ca_cAMP)
    # fig = Processor.plot_rois()
    # fig.savefig(save_path_Ca_cAMP + "rois.jpg")
