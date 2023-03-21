import skimage.io as io
from matplotlib import pyplot as plt


#%%

file = "Data/170424 HN1L K2 OKT3 Beads/170424 2.tif"

img = io.imread(file)

plt.imshow(img[0])
plt.show()

#%%

import tomli

#%%

parameters = dict(path="", nb_rois=3)

#print(parameters)
print(parameters["nb_rois"])