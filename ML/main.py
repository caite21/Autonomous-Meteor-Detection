import os
import random
import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Dropout, Flatten
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter)
from dataclasses import dataclass
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
from keras.preprocessing.image import load_img, img_to_array
from sklearn.metrics import ConfusionMatrixDisplay
import copy as cp
from tensorflow.keras import models

SEED_VALUE = 42
# Fix seed to make training deterministic.
random.seed(SEED_VALUE)
np.random.seed(SEED_VALUE)
tf.random.set_seed(SEED_VALUE)

# Preprocesssing
C_SCALE = 0.00007
THRESH_ADD = 15
HIST_THRESH = 0.8
AREA_THRESH_1 = 0.00005
AREA_THRESH_2 = 0.1
CIRCULAR_THRESH = 0.03
BASE_THRESH = 150
IMG_SIZE = 256

# Compresses image down to desired size. Adds black borders to images that don't
# scale properly
def compress_image(source, size, scale:float):
    shape = source.shape
    x = int(int(shape[0] > shape[1])*(shape[0]-shape[1])/2)
    y = int(int(shape[1] > shape[0])*(shape[1]-shape[0])/2)
    img = cv.copyMakeBorder(source, y, y, x, x, cv.BORDER_CONSTANT, value=[0,0,0])
    img = cv.GaussianBlur(img,(5,5),0)
    img = cv.resize(img, size, fx=scale, fy=scale, interpolation=cv.INTER_AREA)
    return img

# Performs grey-level thresholding on image
def perform_threshold(source, threshold:float, maxvalue:float):
    ret,img = cv.threshold(source,threshold,maxvalue,cv.THRESH_BINARY)
    return img

def preprocess_source(orig, new_size=IMG_SIZE):
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

test_dir = './'
img_dim = 256
test_size = 0.1
X = []
y = []

print("Start image loading")
for filename in os.listdir(test_dir):
    if filename.endswith(".jpg"):
        # img = load_img(os.path.join(test_dir, filename), color_mode='grayscale')
        # img_array = img_to_array(img)
        img_array = cv.imread(test_dir+filename, cv.IMREAD_GRAYSCALE)
        assert img_array is not None, "file could not be read, check provided path exists"
        img_array = preprocess_source(img_array, img_dim)
        X.append(img_array)
        if "2024" in filename:
            y.append(0)
        else:
            y.append(1)

print("Images loaded")

X = np.array(X)
y = np.array(y)
plt.figure(figsize=(18, 9))
num_rows = 1
num_cols = 1
# plot each of the images in the batch and the associated ground truth labels.
for i in range(num_rows*num_cols):
    ax = plt.subplot(num_rows, num_cols, i + 1)
    plt.imshow(X[i,:,:])
    plt.axis("off")

# Normalize images to the range [0, 1].
X = X.astype("float32") / 255

model = models.load_model('cnn.keras')

y_pred = np.round(model.predict(X))
ConfusionMatrixDisplay.from_predictions(y, y_pred)
plt.show()