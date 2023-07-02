from pathlib import Path
import tomli
import os
import json
import time
from stardist.models import StarDist2D
import argparse

from general.processing import ImageProcessor
from GUI import TDarts_GUI
from general.logger import Logger


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
logger = Logger()


def main(gui_enabled):
    if gui_enabled:
        gui = TDarts_GUI()
        gui.run_main_loop()

    start_time = time.time()

    parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
    logger.info(json.dumps(parameters, sort_keys=False, indent=4))

    model = StarDist2D.from_pretrained('2D_versatile_fluo')

    Processor = ImageProcessor(parameters, model, logger)

    # Postprocessing pipeline
    Processor.start_postprocessing()

    # shape normalization
    normalized_cells_dict = Processor.apply_shape_normalization()

    # analysis: hotspot detection and dartboard projection
    Processor.hotspot_detection(normalized_cells_dict)

    Processor.dartboard(normalized_cells_dict)

    Processor.save_image_files()
    Processor.save_ratio_image_files()

    end_time = time.time()
    # execution time
    elapsed_time = end_time - start_time
    print("\n")
    logger.log_and_print(message=f'Execution time: {float(elapsed_time):.1f}, seconds',
                  level=logger.logging.INFO, logger=logger)


if __name__ == "__main__":

    logger.info("Program started")
    parser = argparse.ArgumentParser(description='Run program.')
    parser.add_argument('--no-gui', dest='gui', action='store_false',
                        help='run without graphical interface')
    parser.set_defaults(gui=True)

    args = parser.parse_args()

    main(args.gui)
    logger.info("Program finished")
    quit()
