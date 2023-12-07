from pathlib import Path

import matplotlib.pyplot as plt
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


logger = Logger()

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
ko_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/K2 OKT3"
wt_data_path = "/Users/lwoelk/ICNScloud/PythonPipeline_Testfiles/HN1L/WT OKT3"


#%%
parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))

#parameters["inputoutput"]["start_frame"] = bead_contact_times_KO.loc[0, 'von_min']
#parameters["inputoutput"]["end_frame"] = bead_contact_times_KO.loc[0, 'end']
parameters["inputoutput"]["start_frame"] = 0
parameters["inputoutput"]["end_frame"]   = 5000

parameters["properties"]["list_of_bead_contacts"] = 0
#%%

celltype = "ko"

if celltype == "ko":
    nb_files = len(bead_contact_times_KO)
    savepath_ko = "results_batch/HN1L/K2/"
    os.makedirs(savepath_ko, exist_ok=True)
elif celltype == "wt":
    nb_files = len(bead_contact_times_WT)
    savepath_wt = "results_batch/HN1L/WT/"
    os.makedirs(savepath_wt, exist_ok=True)
else:
    nb_files = 0

logger.info("Program started")
for i in range(nb_files):

    start_time = time.time()
    if celltype == "ko":
        basename = bead_contact_times_KO.loc[i, 'fname']
        filename = ko_data_path + '/' + basename + '.tif'
    elif celltype == "wt":
        basename = bead_contact_times_WT.loc[i, 'fname']
        filename = wt_data_path + '/' + basename + '.tif'
    else:
        basename = None

    Processor = ImageProcessor.fromfilename(filename, parameters)

    # channel registration
    Processor.channel2 = Processor.registration.channel_registration(Processor.channel1, Processor.channel2,
                                                           Processor.parameters["properties"][
                                                               "registration_framebyframe"])

    # background subtraction
    Processor.channel1, Processor.channel2 = Processor.background_subtraction(Processor.channel1, Processor.channel2)

    # segmentation of cells, tracking
    Processor.segmentation_result_dict = {}
    Processor.segmentation_result_dict = Processor.select_rois()

    nb_rois = len(Processor.segmentation_result_dict)
    for n in range(nb_rois):
        try:
            roi_dict = Processor.segmentation_result_dict[n]
            roi_ch1 = roi_dict[0]
            roi_ch2 = roi_dict[1]
        except Exception as E:
            print(E)
            continue

        subpath = basename + "/" + "cell" + str(n) + "/"

        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "0_channel1_beforedecon.tif", roi_ch1)
        io.imsave(savepath_cell + "0_channel2_beforedecon.tif", roi_ch2)


    # deconvolution
    #Processor.deconvolution_result_dict = {}
    Processor.segmentation_result_dict = Processor.deconvolve_cell_images(Processor.segmentation_result_dict)

    nb_rois = len(Processor.segmentation_result_dict)
    for n in range(nb_rois):
        try:
            roi_dict = Processor.segmentation_result_dict[n]
            roi_ch1 = roi_dict[0]
            roi_ch2 = roi_dict[1]
        except Exception as E:
            print(E)
            continue

        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "1_channel1_afterdecon.tif", roi_ch1)
        io.imsave(savepath_cell + "1_channel2_afterdecon.tif", roi_ch2)

    # cell images
    Processor.create_cell_images(Processor.segmentation_result_dict)

    # bleaching correction
    Processor.bleaching_correction()

    for n, cell in enumerate(Processor.cell_list):
        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "2_channel1_afterbleaching.tif", cell.channel1.image)
        io.imsave(savepath_cell + "2_channel2_afterbleaching.tif", cell.channel2.image)

    # first median filter
    Processor.medianfilter("channels")
    for n, cell in enumerate(Processor.cell_list):
        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "3_channel1_aftermedian1.tif", cell.channel1.image)
        io.imsave(savepath_cell + "3_channel2_aftermedian1.tif", cell.channel2.image)

    # generation of ratio images
    Processor.generate_ratio_images()
    for n, cell in enumerate(Processor.cell_list):
        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "4_ratio_beforemedian2.tif", cell.ratio)

    # second median filter
    Processor.medianfilter("ratio")
    for n, cell in enumerate(Processor.cell_list):
        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "5_ratio_aftermedian2.tif", cell.ratio)

    # clear area outside the cells
    Processor.clear_outside_of_cells(Processor.segmentation_result_dict)
    for n,cell in enumerate(Processor.cell_list):
        subpath = basename + "/" + "cell" + str(n) + "/"
        if celltype == "ko":
            savepath_cell = savepath_ko + subpath
        elif celltype == "wt":
            savepath_cell = savepath_wt + subpath
        os.makedirs(savepath_cell, exist_ok=True)
        io.imsave(savepath_cell + "6_ratio_final.tif", cell.ratio)

    end_time = time.time()
    # execution time
    elapsed_time = end_time - start_time
    print("\n")
    logger.log_and_print(message=f'Execution time: {float(elapsed_time):.1f}, seconds',
                         level=logger.logging.INFO, logger=logger)

logger.info("Program finished")
