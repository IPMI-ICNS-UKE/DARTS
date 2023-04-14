import skimage.io as io
import numpy as np

path = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Owncloud/230221_ATPOS_Optimierung_1_w1Dual-CF-488-561-camera2-1-duplicate-10frames.tif"
save_path = "/Users/dejan/Documents/Doktorarbeit/Beispielbilder Segmentierung/Zielordner_Test/"
img = io.imread(path)

min_x = 0
max_x = 200
crop_delta_x = max_x-min_x
min_y = 0
max_y = 200
crop_delta_y = max_y-min_y

number_of_frames = len(img)

cropped_image = img[0:number_of_frames, min_y:max_y, min_x:max_x]
io.imsave(save_path + "cropped_image" + ".tif", cropped_image)
