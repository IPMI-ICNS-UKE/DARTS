from skimage import io
import matplotlib.pyplot as plt
import numpy as np
import cv2

# link to image: https://biotium.com/wp-content/uploads/2018/05/MemBrite-Fix-yeast-mix-magenta.jpg
img_path = "/Users/dejan/Downloads/MemBrite-Fix-488-568-640-yeast-mix.jpg"

img = cv2.imread(img_path, 0)

# smoothing image with gaussian filter
blur = cv2.GaussianBlur(img,(5,5),0, 1.0)

# thresholding image with Otsu-Algorithm
ret,th = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

# ggf. simpleBlobDetector verwenden


while True:
    cv2.imshow('out', th)
    key = cv2.waitKey(0)
    if key == 27:
        break
