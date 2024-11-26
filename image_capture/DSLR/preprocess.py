""" 
    Image preprocessing functions for the CNN of the 
    Autonomous Meteor Detection System
"""

import numpy as np
import cv2 as cv
import copy as cp


# Preprocesssing settings
THRESH_ADD = 15
HIST_THRESH = 0.9
AREA_THRESH_1 = 0.00001
AREA_THRESH_2 = 0.01
CIRCULAR_THRESH = 0.03
BASE_THRESH = 150
IMG_SIZE = 256

def compress_image(source, size, scale:float):
    ''' Compresses image down to desired size. Adds black borders to images that don't scale properly. '''

    shape = source.shape
    x = int(int(shape[0] > shape[1])*(shape[0]-shape[1])/2)
    y = int(int(shape[1] > shape[0])*(shape[1]-shape[0])/2)
    img = cv.copyMakeBorder(source, y, y, x, x, cv.BORDER_CONSTANT, value=[0,0,0])
    img = cv.GaussianBlur(img,(5,5),0)
    img = cv.resize(img, size, fx=scale, fy=scale, interpolation=cv.INTER_AREA)
    return img

def perform_threshold(source, threshold:float, maxvalue:float):
    ''' Performs grey-level thresholding on image. '''

    ret,img = cv.threshold(source,threshold,maxvalue,cv.THRESH_BINARY)
    return img

def preprocess_source(orig, new_size=IMG_SIZE):
    ''' Preprocess image for CNN model by finding bright contours. '''

    copy = cp.copy(orig)

    # Image Constants
    kernel = np.ones((5,5),np.uint8)
    img_area = orig.shape[0] * orig.shape[1]

    # Perform initial thresholding
    target = orig.size * HIST_THRESH
    hist = cv.calcHist([orig],[0],None,[256],[0,256])
    new_thresh = 0
    cumsum = 0
    for b in hist:
        new_thresh += 1
        cumsum += b[0]
        if cumsum >= target:
            break
    if new_thresh < BASE_THRESH:
        new_thresh = BASE_THRESH
    thr1 = perform_threshold(copy, new_thresh, 255)

    # find contours in the binary image
    repeat = False
    contours, _ = cv.findContours(thr1,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
    for c in contours:
        # calculate moments for each contour
        area = cv.contourArea(c)
        area_r = area / img_area
        approx = cv.approxPolyDP(c, CIRCULAR_THRESH * cv.arcLength(c, True), True)
        if ((area_r >= AREA_THRESH_1 and cv.isContourConvex(approx)) or (area_r >= AREA_THRESH_2)):
            if (not repeat):
                repeat = True
            cv.drawContours(copy, [c], 0, (0, 0, 255), -1)

    # Perform secondary thresholding
    thr2 = thr1
    if (repeat):
        thr2 = perform_threshold(copy, new_thresh+THRESH_ADD, 255)

    # Apply morphological operations
    pr1 = cv.dilate(thr2, kernel, iterations=3)
    pr2 = cv.morphologyEx(pr1, cv.MORPH_CLOSE, kernel, iterations=10)

    img_fin = compress_image(pr2, (new_size,new_size), 1)

    return img_fin
