# Autonomous Meteor Detection

<p align="center">
  <img src="https://github.com/user-attachments/assets/39b19f3d-45b6-40fb-8809-7e801bc29ab3" alt="left_star" width="25%"/>
  <img src="https://github.com/user-attachments/assets/75a4ca70-aa70-4f48-8d00-9bebee709458" alt="AMDT_daytime" width="48%"/>
  <img src="https://github.com/user-attachments/assets/8a4e6e3c-ba96-4c75-84b7-f16403438d7f" alt="right_star" width="25%"/>
</p>

## Summary

This project is an autonomous meteor detection and tracking system for hobbyist and research applications. Our client's primary goal was to track meteor trajectories to facilitate the collection of meteorites for research.


The system proposed is an open-source, cost-effective, accessible, and modular system for autonomously detecting meteors, built using readily available commercial-off-the-shelf components. A fully functional prototype was designed, developed, and tested. The prototype design utilized a digital single-lens reflex camera connected to a single-board computer, controlled remotely via a web interface; a local machine learning model running on the single-board computer was deployed to detect meteor occurrences in captured images. A weatherproof housing was constructed to contain the system. Night tests were conducted to confirm the system's effectiveness. The prototype successfully captured images and supported remote system control through the web interface. 


Computer Engineering Capstone Project by Ben Paulson, Caite Sklar, Alex Zeng, and Sagi Kusmanov.

### New Machine Learning

The updated meteor detection pipeline begins by preprocessing the input image and using OpenCV to identify relatively bright lines. These regions are then cropped into 256x256 images, which are fed into a convolutional neural network (CNN). The CNN was trained on a dataset of 3,000 slow-shutter photos of the night sky generously provided by the Desert Fireball Network (DFN). The neural network architecture consists of six convolutional layers and a dropout layer with a 50% rate to enhance generalization. The latest Keras model, version 3.7, is available in the releases, achieving 95% accuracy on the test set and an F1 score of 90%. 

## Photo Gallery
<p align="center">
  <img src="https://github.com/user-attachments/assets/73887b21-072c-41e6-bcf4-1d52034e0a9e" alt="AMDT_daytime" width="32%"/>
  <img src="https://github.com/user-attachments/assets/71bdb65c-1962-485c-9ab0-6220fd80b064" alt="AMDT_inside" width="32%"/>
  <img src="https://github.com/user-attachments/assets/5c1b69d5-7b4e-43a7-967d-e2b14cd67207" alt="closed box" width="32%"/>
  <p> The functional, weatherproof prototype was developed by Ben Paulson, Caite Sklar, Alex Zeng, and Sagi Kusmanov. The system captures slow-shutter photos of the night sky 
  throughout the night (or during a user-configured time period via the website), detects meteors in real-time, and uploads the data to the cloud. </p>
</p>
<br>

<p align="center">
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/preprocess_1.png" alt="AMDT_daytime" width="32%"/>
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/preprocess_2.png" alt="AMDT_inside" width="32%"/>
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/preprocess_3.png" alt="closed box" width="32%"/>
  <p> The first step in the meteor detection process is isolating areas of relatively bright lines using OpenCV. These regions are then cropped into separate 256x256 images for the CNN. </p>
</p>
<br>

<p align="center">
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/prediction_1.png" alt="AMDT_daytime" width="32%"/>
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/prediction_2.png" alt="AMDT_inside" width="32%"/>
  <img src="https://github.com/caite21/Autonomous-Meteor-Detection/blob/main/machine_learning/images/prediction_3.png" alt="closed box" width="32%"/>
  <p>Each cropped image is classified as either "Meteor" or "Non-Meteor" by the convolutional neural network (CNN). The prediction threshold of model v3.7 is 0.8. </p>
</p>
<br>

## Presentation Poster
[AMDT_Poster.pdf](https://github.com/user-attachments/files/16999669/ECE492_AMDT2_Poster_V02.pdf)
![AMDT_Group_Poster](https://github.com/user-attachments/assets/06198668-9c31-4774-b4a9-852616c7491c)

