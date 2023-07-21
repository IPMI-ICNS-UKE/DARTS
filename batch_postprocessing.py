from pathlib import Path
import tomli
import os
import json
import time
from stardist.models import StarDist2D
import argparse
import skimage.io as io
from general.processing import ImageProcessor
from GUI import TDarts_GUI
from general.logger import Logger
from analysis.Bead_Contact_GUI import BeadContactGUI
from analysis.MeanDartboard import MeanDartboardGenerator
import pandas as pd
import numpy as np





Processor = ImageProcessor(file, list_of_bead_contacts_for_file, parameters, model, logger)
        print("Now processing the following file: " + file)
        # Postprocessing pipeline
        Processor.start_postprocessing()