from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor


def main():

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

    Processor  = ImageProcessor(parameters)
    Processor.select_rois()
    Processor.start_postprocessing()
    Processor.save_image_files()  # save processed cropped images


if __name__ == '__main__':
    main()