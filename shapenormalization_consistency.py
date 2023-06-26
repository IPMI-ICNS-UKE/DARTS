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
import pandas as pd

#%%

folder = "/Users/lwoelk/PycharmProjects/T-DARTS/Data/K2"
results_dir = "results/normalizationcomparison/"

os.makedirs(results_dir, exist_ok=True)

parameters = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
model = StarDist2D.from_pretrained('2D_versatile_fluo')

for file in os.listdir(folder):
     filename = os.fsdecode(file)
     if filename.endswith(".tif") or filename.endswith(".tiff"):
        parameters["inputoutput"]["path_to_input_combined"] = folder + "/" + filename
        print("processing image ", parameters["inputoutput"]["path_to_input_combined"])

        parameters["inputoutput"]["start_frame"] = None
        parameters["inputoutput"]["end_frame"] = None

        fname_short = Path(parameters["inputoutput"]["path_to_input_combined"]).stem

        Processor = ImageProcessor(parameters, model)

        Processor.start_postprocessing()

        for i, cell in enumerate(Processor.cell_list):
            normalized_ratio, centroid_coords = Processor.normalize_cell_shape(cell)

            t=0
            fig, ax = plt.subplots(ncols=2)
            ax[0].imshow(cell.ratio[t])
            ax[1].imshow(normalized_ratio[t])
            for ax_i in ax.reshape(-1):
                ax_i.axis('off')
            fig.savefig(results_dir + fname_short + '_shapecomp_cell'+str(i)+ '_t'+str(t)+'.jpg')


            mean_r = pd.Series(cell.ratio.mean(axis=(1,2))/ cell.ratio.mean(axis=(1,2)).max())
            mean_n = pd.Series(normalized_ratio.mean(axis=(1,2))/normalized_ratio.mean(axis=(1,2)).max())

            area_n = pd.Series(np.count_nonzero(normalized_ratio, axis=(1,2)) / np.count_nonzero(normalized_ratio, axis=(1,2)).max())
            area_r = pd.Series(np.count_nonzero(cell.ratio, axis=(1,2)) / np.count_nonzero(cell.ratio, axis=(1,2)).max())

            window_size = 100

            fig, ax = plt.subplots()
            ax.plot(area_r.rolling(window=window_size).mean(), color='r')
            ax.plot(area_n.rolling(window=window_size).mean(), ':', color='r')
            ax.plot(mean_r.rolling(window=window_size).mean(), color='b')
            ax.plot(mean_n.rolling(window=window_size).mean(), ':', color='b')
            ax.set_ylabel('normalized to maximum value')
            ax.set_xlabel('t')
            fig.savefig(results_dir + fname_short + '_areamean_cell'+str(i)+ '_t'+str(t)+'.jpg')



