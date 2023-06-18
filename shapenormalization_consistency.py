import time
import matplotlib.pyplot as plt
from pathlib import Path
import tomli
from postprocessing.processing import ImageProcessor
from pystackreg import StackReg
import SimpleITK as sitk
import numpy as np
from stardist.models import StarDist2D
from csbdeep.utils import normalize
from postprocessing.shapenormalization import ShapeNormalization
import os

#%%

folder = "/Users/lwoelk/PycharmProjects/T-DARTS/Data/K2"




parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

for file in os.listdir(folder):
     filename = os.fsdecode(file)
     if filename.endswith(".tif") or filename.endswith(".tiff"):
        parameters["inputoutput"]["path_to_input_combined"] = folder + "/" + filename
        print("processing image ", parameters["inputoutput"]["path_to_input_combined"])

        Processor = ImageProcessor(parameters)

        Processor.start_postprocessing()

