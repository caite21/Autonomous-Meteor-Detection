# -*- coding: utf-8 -*-
"""Train_Meteor_CNN.ipynb

# Training Meteor CNN

Upload preprocessed images and run in Google Colab.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import random
import cv2
from PIL import Image

from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.preprocessing import image
from sklearn.metrics import classification_report

from google.colab import files


"""## Settings"""

# Data folders
Training_Pos_Folder = 'Train_Meteor'
Training_Neg_Folder = 'Train_Not_Meteor'
Testing_Pos_Folder = 'Test_Meteor'
Testing_Neg_Folder = 'Test_Not_Meteor'

# Image dimensions
img_width = 256
img_height = img_width
img_color_channels = 3

# Class names
class_weights = {0: 1.0, 1: 3.0}
class_names = ['Not_Meteor', 'Meteor']

def load_images_from_folder(folder, label, images, labels):
    """Load images from folder, label them, and append to the image and label lists."""
    if len(os.listdir(folder)) == 0:
        print(f"Error: {folder} is empty.")
        return -1
    for filename in os.listdir(folder):
        if filename.endswith('.jpg'):
            img = cv2.imread(os.path.join(folder, filename))
            if img.shape[0] == img_width and img.shape[1] == img_height:
                images.append(img)
                labels.append(label)
            else:
                print(f"Error: Image in folder {folder} is wrong shape: {img.shape}. Expected: {(img_width, img_height, img_color_channels)}.")
                resized = cv2.resize(img, (img_width, img_height), interpolation=cv2.INTER_LANCZOS4)
                images.append(resized)
                labels.append(label)
                print("Fixed", resized.shape)


def preprocess_images(images):
    """Normalize images."""
    return np.array(images) / 255.0

def load_data(Training_Neg_Folder, Training_Pos_Folder, Testing_Neg_Folder, Testing_Pos_Folder):
    train_images, train_labels = [], []
    test_images, test_labels = [], []

    # Load the training and testing data
    load_images_from_folder(Training_Neg_Folder, 0, train_images, train_labels)
    load_images_from_folder(Training_Pos_Folder, 1, train_images, train_labels)
    load_images_from_folder(Testing_Neg_Folder, 0, test_images, test_labels)
    load_images_from_folder(Testing_Pos_Folder, 1, test_images, test_labels)

    # Preprocess the images
    train_images = preprocess_images(train_images)
    test_images = preprocess_images(test_images)

    train_labels = np.array(train_labels)
    test_labels = np.array(test_labels)

    return train_images, test_images, train_labels, test_labels

def get_model():
    model = Sequential([
        Conv2D(32, (3, 3), activation='relu', input_shape=(img_width, img_height, img_color_channels)),
        MaxPooling2D((2, 2)),
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Conv2D(128, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Conv2D(256, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Conv2D(256, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        Conv2D(256, (3, 3), activation='relu'),
        Flatten(),
        Dense(256, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model

def plot_predictions(y_pred):
    plt.figure(figsize=(10,10))
    ploti = 0
    for i in range(len(y_pred)):
        plt.subplot(int(len(y_pred)/5) + 1, 5, ploti+1)
        plt.axis('off')
        plt.imshow(x_test[i])
        plt.title(f"{y_test[i] == y_pred[i]}: {class_names[y_pred[i]]}")
        ploti += 1
    plt.show()

def evaluate_predictions(y_pred_prob, y_test, print_vals=False, plot=False):
    # Convert probabilities to binary predictions
    pred_threshold = 0.8
    y_pred = (y_pred_prob > pred_threshold).astype(int).flatten()

    # Print report
    print(classification_report(y_test, y_pred))

    if print_vals:
        # Print all prediction values
        print("Probability\t Pred\t Correct")
        for i in range(len(y_pred_prob)):
            print(y_pred_prob[i][0], " \t", y_pred[i] , " ", y_test[i])

    if plot:
        plot_predictions(y_pred[ (len(y_pred) - 16): ])


"""## Train"""

x_train, x_test, y_train, y_test = load_data(Training_Neg_Folder, Training_Pos_Folder, Testing_Neg_Folder, Testing_Pos_Folder)

model = get_model()
model.fit(x_train, y_train, epochs=10, validation_data=(x_test, y_test), class_weight=class_weights)

"""Evaluate training:"""

y_pred_prob_train = model.predict(x_train)

evaluate_predictions(y_pred_prob_train, y_train, print_vals=False, plot=False)


"""## Test"""

# Predict probabilities for test images
y_pred_prob = model.predict(x_test)

evaluate_predictions(y_pred_prob, y_test, print_vals=True, plot=False)


"""## Save"""

model.save("CNN_Meteors_v3.7.keras")
files.download('CNN_Meteors_v3.7.keras')