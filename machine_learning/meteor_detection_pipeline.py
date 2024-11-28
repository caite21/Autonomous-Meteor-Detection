# -*- coding: utf-8 -*-
"""Meteor_Detection_Pipeline.ipynb

# Meteor Detection Full Pipeline

Upload the model and a set of night sky images to Google Colab.

The code will display the images along with the model's predictions, indicating 
whether each image contains a meteor.
"""

model_name = "CNN_Meteors_v3.7.keras"
model_threshold = 0.8



import cv2
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model

class_names = ['Not Meteor', 'Meteor']


"""### OpenCV Bound Bright Lines"""

def adjust_square_bounds(min_val, max_val, crop_size, limit):
    """Ensures square crop bounds stay within image limits."""
    if max_val - min_val < 2 * crop_size:
        if min_val == 0:
            max_val = min(limit, 2 * crop_size)
        elif max_val == limit:
            min_val = max(0, limit - 2 * crop_size)
    return min_val, max_val

def crop_bright_lines(filename, crop_size=256):
    """
    Detects bright contours in an image, crops square regions around them,
    and returns the cropped images.

    Returns:
        List of cropped images.
    """
    image = cv2.imread(filename)

    if image is None:
        print("Image not found.")
        return

    img_height, img_width = image.shape[:2]

    # Resize
    compress_size = 1024
    if img_height > compress_size:
        compress_width = int(img_width/img_height*compress_size)
        image = cv2.resize(image, (compress_width, compress_size), interpolation=cv2.INTER_LANCZOS4)

    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title(f"Original: {filename}")
    plt.show()

    img_height, img_width = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to isolate bright regions
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, -40)

    # Edge detection
    edges = cv2.Canny(thresh, 30, 255)

    # Detect lines using Hough Transform
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=20, minLineLength=15, maxLineGap=5)

    detected_regions = []
    cropped_images = []

    # Bound the detected lines
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Compute the bounding box
            x_min = min(x1, x2)
            y_min = min(y1, y2)
            x_max = max(x1, x2)
            y_max = max(y1, y2)
            x_cen = int((x_max - x_min) / 2) + x_min
            y_cen = int((y_max - y_min) / 2) + y_min

            # Compute crop bounds
            half_crop_size = int(crop_size / 2)
            x_min_crop = max(0, x_cen - half_crop_size)
            x_max_crop = min(img_width, x_cen + half_crop_size)
            y_min_crop = max(0, y_cen - half_crop_size)
            y_max_crop = min(img_height, y_cen + half_crop_size)

            # Ensure square crops within bounds
            x_min_crop, x_max_crop = adjust_square_bounds(x_min_crop, x_max_crop, half_crop_size, img_width)
            y_min_crop, y_max_crop = adjust_square_bounds(y_min_crop, y_max_crop, half_crop_size, img_height)

            # Check for overlapping regions with a threshold of 10 pixels
            overlap = 50
            too_close = False
            for existing_region in detected_regions:
                ex_min_x, ex_max_x, ex_min_y, ex_max_y = existing_region

                # Check overlap conditions (maximum allowed overlap is 10 pixels)
                if not (
                    x_max_crop <= ex_min_x + overlap
                    or x_min_crop >= ex_max_x - overlap
                    or y_max_crop <= ex_min_y + overlap
                    or y_min_crop >= ex_max_y - overlap
                ):
                    too_close = True
                    break

            if too_close:
                continue  # Skip this region if it overlaps too much


            detected_regions.append((x_min_crop, x_max_crop, y_min_crop, y_max_crop))
            cropped_image = image[y_min_crop:y_max_crop, x_min_crop:x_max_crop]
            cropped_images.append(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))

    return cropped_images


"""### Meteor Detection CNN"""

myModel = load_model(model_name)


"""## Predict Images

OpenCV takes a first pass at detecting a meteor by finding areas of the image where there are bright lines. It can take large non-square images. The areas are then processed and passed to the CNN for classification.
"""

def cnn_predict(image_path):
    sub_images = crop_bright_lines(image_path, crop_size=256)

    final_prediction = class_names[0]
    for img_arr in sub_images:
        img_arr = img_arr / 255.0
        img_arr_exp = np.expand_dims(img_arr, axis=0)

        pred_val = myModel.predict(img_arr_exp)[0][0]
        pred_threshold = model_threshold
        pred_class = class_names[ (pred_val > pred_threshold).astype(int) ]

        plt.imshow(img_arr)
        plt.title(f"Sub-Prediction: {pred_class} {pred_val}")
        plt.show()

        if pred_class == class_names[1]:
            final_prediction = pred_class

    print(f"Final prediction of {image_path}: {final_prediction}\n\n")
    return final_prediction

# Predict all uploaded images
import os
all_predictions = []
for filename in os.listdir():
    if filename.endswith('.jpg') :
        all_predictions.append((filename, cnn_predict(filename)))

print("\nAll Predictions:")
for p in all_predictions:
    print(p[0], '\t', p[1])