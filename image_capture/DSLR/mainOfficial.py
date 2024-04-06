from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import time
import signal, os, subprocess
import os
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage
import warnings
from apscheduler.schedulers.background import BackgroundScheduler

# Firebase Key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "amdt-a1b24-firebase-adminsdk-q32q3-c9217e3b84.json"

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
    
    # set var:
    isMeteor = False
    print("Running -\t ML detection result:", isMeteor)
    
    # upload asynchronously
    uploadImageScheduler.add_job(uploadImage)
    

def uploadImage():
    uploadFromFolder()
    print("Running -\t Image uploaded")
    
    
def read_sys_config():
    global start
    global end

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
    # FOR THE LOVE OF GOD DONT TOUCH THIS
    os.chdir(save_location)
    print("Running -\t Initializing")
    
    # get start and end time from firebase once
    global start
    global end
    global contCamSystemFlag
    contCamSystemFlag = True
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
    
    print("Running -\t System started up")

    try:
        # start checking firebase every x and updates global vars
        checkConfigScheduler.add_job(read_sys_config, 'interval', seconds=5)
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
            print("start end now:", start, end, datetime.now() )
            
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





