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

#%%

def list_files(directory, extension):
    filenames = []
    for filename in os.listdir(directory):
        if filename.endswith(extension):
            filenames.append(os.path.splitext(filename)[0])
    return filenames

#%%
bead_contact_times_KO = pd.read_csv("bead_contact_times_KO.csv")
bead_contact_times_WT = pd.read_csv("bead_contact_times_WT.csv")
#%%

ko_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/K2 OKT3"
wt_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/WT OKT3"

#%%
parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

filename = ko_data_path + '/' + bead_contact_times_KO.loc[0, 'fname'] + '.tif'
#%%

Processor = ImageProcessor.fromfilename(filename, parameters)

# channel registration
Processor.channel2 = Processor.registration.channel_registration(Processor.channel1, Processor.channel2,
                                                       Processor.parameters["properties"][
                                                           "registration_framebyframe"])

# background subtraction
Processor.channel1, Processor.channel2 = Processor.background_subtraction(Processor.channel1, Processor.channel2)

# segmentation of cells, tracking
Processor.segmentation_result_dict = Processor.select_rois()



#%%

# deconvolution
Processor.segmentation_result_dict = Processor.deconvolve_cell_images(Processor.segmentation_result_dict)

# cell images
Processor.create_cell_images(Processor.segmentation_result_dict)

# bleaching correction
Processor.bleaching_correction()

# first median filter
Processor.medianfilter("channels")

# generation of ratio images
Processor.generate_ratio_images()

# second median filter
Processor.medianfilter("ratio")

# clear area outside the cells
Processor.clear_outside_of_cells(Processor.segmentation_result_dict)

