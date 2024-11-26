"""
    Main file for Autonomous Meteor Detection System

    Description: Schedules 4 threads to handle the following tasks: configure when to run and stop 
        which is set by the user on the website, trigger the camera to take a photo, 
        predict whether image contains a meteor with the CNN model, and upload the 
        image to Firebase (Google cloud storage). 
"""

import wifi
import preprocess
import capture


import os
import shutil
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage

import tensorflow as tf
from tensorflow.keras import models



def camera_task():
    ''' Trigger gPhoto to take a photo repeatedly until cancelled and print time taken. '''

    print("Running -\t Camera system initializing")
    
    wifi.wait_for_wifi()
    
    timer_start = time.time()
    capture.trigger_capture()
    timer_end = time.time()
    print("Running -\t Camera ran for", timer_end - timer_start)
    
    # Classify asynchronously
    CNNScheduler.add_job(CNN_task)
    
    # Schedule camera_task task again
    if system_on_flag:
        camSystemScheduler.add_job(camera_task)
 
def CNN_task():
    ''' Preprocess and use model to predict every image in current directory. '''

    print("Running -\t ML starting")
    isMeteor = False
    
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

            img_array = preprocess.preprocess_source(img_array, IMG_SIZE)
            img_array = img_array.astype("float32") / 255

            pred = int(np.round(model.predict([img_array])))
            if pred == 1:
                isMeteor = True
            else:
                isMeteor = False
    
    print("Running -\t ML detection result:", isMeteor)
    
    # Upload asynchronously
    uploadImageScheduler.add_job(upload_images_task)

def upload_image(filename, local_image_path):
    ''' Upload image file to firebase if they haven't already been uploaded. ''' 

    storage_client = storage.Client()
    bucket = storage_client.bucket('amdt-a1b24.appspot.com')
    
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        # Check if the file already exists in Firebase Storage
        blob = bucket.blob(filename)
        if blob.exists():
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
            "isMeteor": isMeteor
        }
        db.collection('images_metadata').document(filename).set(metadata)

        print(f"Image '{filename}' uploaded to Firebase Storage")
        shutil.move(local_image_path, "/home/amdt/Desktop/old_photos/"+filename)

def upload_images_task():
    ''' Upload all images in current directory to firebase if they haven't been uploaded yet. ''' 

    print("Running -\t Image uploaded")
    # Path to the directory containing images to upload
    downloads_dir = "/home/amdt/Desktop/AMDT/image_capture/DSLR"
    
    # Iterate through the files and upload
    files = os.listdir(downloads_dir)
    for file_name in files:
        file_path = os.path.join(downloads_dir, file_name)
        upload_image(file_name, file_path)

def read_config_task():
    ''' Read when the system has been configured to start and end by the user from firebase. '''

    wifi.wait_for_wifi()

    # Get data from the document
    doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        
        # Parse start and end time
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
  


if __name__ == '__main__':
    # Initialize Firebase
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "amdt-a1b24-firebase-adminsdk-q32q3-c9217e3b84.json"
    default_app = firebase_admin.initialize_app()
    global db
    db = firestore.Client()

    print("Running -\t Initializing")
    capture.kill_gphoto()
    save_location = "/home/amdt/Desktop/AMDT/image_capture/DSLR"
    os.chdir(save_location)
    global system_on_flag
    system_on_flag = False

    # Don't start until connected to wifi
    print("Connecting to the Internet..")
    wifi.wait_for_wifi()
    print("Connected to WiFi")
    
    # Get start and end time from firebase once
    global start, end
    read_config_task()

    # Task schedulers
    global camSystemScheduler, checkConfigScheduler, uploadImageScheduler, CNNScheduler
    camSystemScheduler = BackgroundScheduler()
    checkConfigScheduler = BackgroundScheduler()
    uploadImageScheduler = BackgroundScheduler()
    CNNScheduler = BackgroundScheduler()
    
    print("Loading Neural Network...")
    global model
    model = models.load_model('cnn.keras')
    print("Running -\t System started up")

    try:
        # Check firebase every x seconds and update global variables
        checkConfigScheduler.add_job(read_config_task, 'interval', seconds=20)
        
        # Initialize all processes
        checkConfigScheduler.start()
        camSystemScheduler.start()
        uploadImageScheduler.start()
        CNNScheduler.start()

        print("Running -\t Started configuration process")

        while True:
            # Start if in set time range and not already running
            if datetime.now() >= start and datetime.now() < end and not system_on_flag:
                print("Running -\t Starting new system iteration")
                system_on_flag = True
                camSystemScheduler.add_job(camera_task, 'date')
            
            # Stop if not in set time range and running
            if (datetime.now() < start or datetime.now() >= end) and system_on_flag:
                print("Running -\t Resetting system iteration")
                system_on_flag = False
            
    except (KeyboardInterrupt, SystemExit):
        print("\nStopping -\t Quitting program from keyboard command")

        # Gracefully quit
        if checkConfigScheduler.running:
            checkConfigScheduler.shutdown()
        if camSystemScheduler.running:
            camSystemScheduler.shutdown()
        if uploadImageScheduler.running:
            uploadImageScheduler.shutdown()
        if CNNScheduler.running:
            CNNScheduler.shutdown()
