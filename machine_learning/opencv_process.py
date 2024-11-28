# -*- coding: utf-8 -*-
"""OpenCV_Process.ipynb

# Process of Bright Line Detection

This process takes an image, compresses it, applies various OpenCV functions
 to identify bright lines, and crops those bright lines into square images to 
 be predicted as meteor or non-meteor later by the CNN.

Upload images and run code in Google Colab to try.

"""

import os
import random
import numpy as np
from datetime import datetime
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

compress_size=1024
crop_size = 256
crops_limit = 3

def adjust_square_bounds(min_val, max_val, crop_size, limit):
    """Ensures square crop bounds stay within image limits."""
    if max_val - min_val < 2 * crop_size:
        if min_val == 0:
            max_val = min(limit, 2 * crop_size)
        elif max_val == limit:
            min_val = max(0, limit - 2 * crop_size)
    return min_val, max_val

def crop_bright_lines(image, crop_size=100):
    if image is None:
        print("Image not found.")
        return

    img_height, img_width = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold to isolate bright regions
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, -40)

    # Edge detection
    edges = cv2.Canny(thresh, 30, 255)

    # Detect lines using Hough Transform
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=20, minLineLength=15, maxLineGap=5)

    # Create a copy of the original image to draw on
    line_image = image.copy()
    detected_regions = []
    cropped_images = []

    # Draw the detected lines
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Compute the bounding box
            x_min = min(x1, x2)
            y_min = min(y1, y2)
            x_max = max(x1, x2)
            y_max = max(y1, y2)

            # Draw the bounding box
            cv2.rectangle(line_image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 1)

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
            # cropped_images.append(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
            cropped_images.append(cropped_image)


    for x_min, x_max, y_min, y_max in detected_regions:
      cv2.rectangle(line_image, (x_min, y_min), (x_max, y_max), (0,255,0), 1)

    # Display the results
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title('Compressed Image')
    plt.show()
    plt.imshow(edges)
    plt.title('Threshold and Edge Detection')
    plt.show()
    plt.imshow(cv2.cvtColor(line_image, cv2.COLOR_BGR2RGB))
    plt.title('Line Detection and Cropped Areas')
    plt.show()

    return cropped_images



# Create a timestamped folder to save the cropped images
# timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
# save_folder = f'compress1228_{timestamp}'
# os.makedirs(save_folder, exist_ok=True)

count = 0
# Loop through each image in the folder
for filename in os.listdir():
    if filename.endswith('.jpg'):
        img = cv2.imread(filename)
        if img is None:
            raise ValueError("Image could not be loaded.")

        # Get the dimensions of the image
        img_height, img_width = img.shape[:2]

        # Resize
        if img_height > compress_size:
            compress_width = int(img_width/img_height*compress_size)
            resized = cv2.resize(img, (compress_width, compress_size), interpolation=cv2.INTER_LANCZOS4)
        else:
            resized = img

        cropped_images = crop_bright_lines(resized, crop_size=256)

        # crop_count = 0
        # for cimg in cropped_images:
        #   # save_path = f'{save_folder}/{count}-{crop_count}.jpg'
        #   # cv2.imwrite(save_path, cimg)

        #   crop_count += 1
        #   if crop_count > crops_limit:
        #       break
        # count += 1
print('Done')