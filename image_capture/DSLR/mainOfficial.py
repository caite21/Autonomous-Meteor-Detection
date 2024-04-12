from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import time
import numpy as np
import signal, os, subprocess
import os
import random
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage
import warnings
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import cv2 as cv
import tensorflow as tf
from keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras import models
import cv2 as cv
import tensorflow as tf
import copy as cp
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Conv2D, MaxPooling2D, Dropout, Flatten
from tensorflow.keras.datasets import cifar10
from tensorflow.keras.utils import to_categorical
from dataclasses import dataclass
import shutil

# Firebase Key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "amdt-a1b24-firebase-adminsdk-q32q3-c9217e3b84.json"

# Preprocesssing
THRESH_ADD = 15
HIST_THRESH = 0.9
AREA_THRESH_1 = 0.00001
AREA_THRESH_2 = 0.01
CIRCULAR_THRESH = 0.03
BASE_THRESH = 150
IMG_SIZE = 256

SEED_VALUE = 42
# Fix seed to make training deterministic.
random.seed(SEED_VALUE)
np.random.seed(SEED_VALUE)
tf.random.set_seed(SEED_VALUE)

import subprocess

def what_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split(':')[1]
    else:
        return ''

def is_connected_to(ssid: str):
    return what_wifi() == ssid

def scan_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split('\n')
    else:
        return []
        
def is_wifi_available(ssid: str):
    return ssid in [x.split(':')[0] for x in scan_wifi()]

def wait_for_wifi():
    ssid = "test"
    password = 'key'
    while not is_wifi_available(ssid):
        pass
    if not is_connected_to(ssid):
        print("Wi-Fi found, trying to connect")
        subprocess.call(['nmcli', 'd', 'wifi', 'connect', ssid, 'password', password])

def connect_to_saved(ssid: str):
    if not is_wifi_available(ssid):
        return False
    subprocess.call(['nmcli', 'c', 'up', ssid])
    return is_connected_to(ssid)



# Compresses image down to desired size. Adds black borders to images that don't scale properly
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

def internet():
    try:
        res = requests.get("https://console.firebase.google.com/u/2/project/amdt-a1b24")
        return True
    except requests.ConnectionError:
        return False
    

# Initialize Firebase
default_app = firebase_admin.initialize_app()
db = firestore.Client()

def upload_image(filename, local_image_path):
    
    storage_client = storage.Client()
    bucket = storage_client.bucket('amdt-a1b24.appspot.com')
    
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        # Check if the file already exists in Firebase Storage
        blob = bucket.blob(filename)
        if blob.exists():
            #print(f"File '{filename}' already exists in Firebase Storage. Skipping upload.")
            return

        # Upload the local image file to Firebase Storage
        blob.upload_from_filename(local_image_path)

        # Get creation time atetime.dof the file
        creation_time = datetime.fromtimestamp(os.path.getctime(local_image_path))

        # Save metadata to Firestore with filename as document name
        metadata = {
            "filename": filename,
            "upload_date": datetime.now().isoformat(),
            "creation_time": creation_time.isoformat(),
            "isMeteor": isMeteor,
            # Add any other metadata you want to save
        }
        db.collection('images_metadata').document(filename).set(metadata)

        print(f"Image '{filename}' uploaded to Firebase Storage")
        shutil.move(local_image_path, "/home/amdt/Desktop/old_photos/"+filename)


def uploadFromFolder():
    
    # Path to the directory containing images you want to upload
    downloads_dir = "/home/amdt/Desktop/AMDT/image_capture/DSLR"
    
    # Iterate through the files and upload
    files = os.listdir(downloads_dir)
    for file_name in files:
        file_path = os.path.join(downloads_dir, file_name)
        upload_image(file_name, file_path)


# Kill the gphoto process that starts
# whenever we turn on the camera or
# reboot the raspberry pi
def killGphoto2Process():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    # Search for the process we want to kill
    for line in out.splitlines():
        if b'gvfsd-gphoto2' in line:
            # Kill that process!
            pid = int(line.split(None,1)[0])
            os.kill(pid, signal.SIGKILL)


shot_date = datetime.now().strftime("%Y-%m-%d") # This has been written to the while True loop.
shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # This has been written to the while True loop.
picID = "PiShots"

clearCommand = ["--folder", "/store_00020001/DCIM/100CANON", \
                "--delete-all-files", "-R"]
# this line captures image and downloads it
# maybe we can separate them? multithreading!
# main thread will take photos, another thread will download them
# current solution takes 37 seconds to take a 30s exposure photo
# ps for sagi: delete photos off camera, they are labelled as IMG_*
# camera captures images and stores them internally, we just download
# them off of it, fix it
triggerCommand = ["--capture-image-and-download"]

folder_name = shot_date + picID
save_location = "/home/amdt/Desktop/AMDT/image_capture/DSLR"


def captureImages():
    gp(triggerCommand)


def renameFiles(ID):
    for filename in os.listdir("."):
        if len(filename) < 13:
            if filename.endswith(".JPG"):
                os.rename(filename, (shot_time + ID + ".JPG"))
                print("Renamed the JPG")
            elif filename.endswith(".CR2"):
                os.rename(filename, (shot_time + ID + ".CR2"))
                print("Renamed the CR2")


killGphoto2Process()

def cameraSystem():
    print("Running -\t Camera system initializing")
    
    wait_for_wifi()

    shot_date = datetime.now().strftime("%Y-%m-%d")
    shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    timer_start = time.time()
    captureImages()
    timer_end = time.time()
    print("Running -\t Camera ran for", timer_end - timer_start)
    
    # classify asynchronously
    CNNScheduler.add_job(CNN)
    
    # schedule cameraSystem task again
    if contCamSystemFlag:
        camSystemScheduler.add_job(cameraSystem)
    
    
def CNN():
    print("Running -\t ML starting")
    global isMeteor
    isMeteor = False
    
    # paste ML stuff here
    
    # Path to the directory containing images to be preprocessed
    downloads_dir = "/home/amdt/Desktop/AMDT/image_capture/DSLR"
    
    # Iterate through the files and upload
    files = os.listdir(downloads_dir)
    for file_name in files:
        file_path = os.path.join(downloads_dir, file_name)
        if file_name.endswith(".jpg"):
            img_array = cv.imread(file_path, cv.IMREAD_GRAYSCALE)
            if img_array is None:
                print(file_name, " file could not be read, check provided path exists")
                continue
            img_array = preprocess_source(img_array, IMG_SIZE)
            img_array = img_array.astype("float32") / 255
            pred = int(np.round(model.predict([img_array])))
            if pred == 1:
                isMeteor = True
            else:
                isMeteor = False
    
    # set var:
    print("Running -\t ML detection result:", isMeteor)
    
    # upload asynchronously
    uploadImageScheduler.add_job(uploadImage)
    

def uploadImage():
    uploadFromFolder()
    print("Running -\t Image uploaded")
    
    
def read_sys_config():
    global start
    global end
    
    wait_for_wifi()

    # Reference to the document
    doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")
    
    # Retrieve the document snapshot
    doc = doc_ref.get()
    
    if doc.exists:
        # Get data from the document
        data = doc.to_dict()
        
        # Print the values
        end_date_str = data.get("EndDate")
        end_time_str = data.get("EndTime")
        start_date_str = data.get("StartDate")
        start_time_str = data.get("StartTime")
        
        year, month, day = map(int, start_date_str.split('-'))
        hour, minute, second = map(int, start_time_str.split(':'))
        start = datetime(year, month, day, hour, minute, second)
        
        year, month, day = map(int, end_date_str.split('-'))
        hour, minute, second = map(int, end_time_str.split(':'))
        end = datetime(year, month, day, hour, minute, second)
        
        print("Running -\t Read time:", start, "to", end)
    
    else:
        print("Error -\t Document does not exist")
  
  
def dummyCam():
    
    global cam_job
    print("in cam")
    if contCamSystemFlag:
        cam_job = camSystemScheduler.add_job(dummyCam)
    dum = 0
    for i in range(100000):
        dum += 2
    

if __name__ == '__main__':
    # don't start until connected to wifi
    print("Connecting to the Internet..")
    wait_for_wifi()
    print("Connected to WiFi")
    
    # FOR THE LOVE OF GOD DONT TOUCH THIS
    os.chdir(save_location)
    print("Running -\t Initializing")
    
    # get start and end time from firebase once
    global start
    global end
    global contCamSystemFlag
    contCamSystemFlag = False
    read_sys_config()

    # concurrent schedulers
    global camSystemScheduler
    global checkConfigScheduler
    global uploadImageScheduler
    global CNNScheduler
    camSystemScheduler = BackgroundScheduler()
    checkConfigScheduler = BackgroundScheduler()
    uploadImageScheduler = BackgroundScheduler()
    CNNScheduler = BackgroundScheduler()
    
    print("Loading Neural network...")
    global model
    model = models.load_model('cnn.keras')
    
    print("Running -\t System started up")

    try:
        # start checking firebase every x and updates global vars
        checkConfigScheduler.add_job(read_sys_config, 'interval', seconds=20)
        # initialize all processes
        checkConfigScheduler.start()
        camSystemScheduler.start()
        uploadImageScheduler.start()
        CNNScheduler.start()
        print("Running -\t Started configuration process")
        while True:
            # if in target and not already running, start proc
            if datetime.now() >= start and datetime.now() < end and not contCamSystemFlag:
                print("Running -\t Starting new system iteration")
                contCamSystemFlag = True
                camSystemScheduler.add_job(cameraSystem, 'date')
            
            # elif not in target and running
            if (datetime.now() < start or datetime.now() >= end) and contCamSystemFlag:
                print("Running -\t Resetting system iteration")
                # camSystemScheduler.shutdown()\
                # cam_job.remove()
                contCamSystemFlag = False
            
            # else: do nothing
            # print("start end now:", start, end, datetime.now() )
            
    except (KeyboardInterrupt, SystemExit):
        # gracefully quit
        print("\nStopping -\t Quitting program from keyboard command")
        if checkConfigScheduler.running:
            checkConfigScheduler.shutdown()
        if camSystemScheduler.running:
            camSystemScheduler.shutdown()
        if uploadImageScheduler.running:
            uploadImageScheduler.shutdown()
        if CNNScheduler.running:
            CNNScheduler.shutdown()
        
             
    
            






""" DONT EVER RUN THIS IN GEANY, RUN IN THE TERMINAL!!!!! ********************************************************************

HOW TO RUN PROCEDURE

DO THIS:
1.) Find path using: find / -type d -name 'bin' 2>/dev/null | grep 'env'
2.) Activate venv using: source /home/amdt/Desktop/AMDT/image_capture/DSLR/.venv/bin/activate
3.) Deactivate venv using: deactivate




"""





