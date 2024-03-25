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
from datetime import datetime
import datetime
import warnings
import time

# Turn off all warnings
warnings.filterwarnings("ignore")

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
            print(f"File '{filename}' already exists in Firebase Storage. Skipping upload.")
            return

        # Upload the local image file to Firebase Storage
        blob.upload_from_filename(local_image_path)

        # Get creation time of the file
        creation_time = datetime.datetime.fromtimestamp(os.path.getctime(local_image_path))

        # Save metadata to Firestore with filename as document name
        metadata = {
            "filename": filename,
            "upload_date": datetime.datetime.now().isoformat(),
            "creation_time": creation_time.isoformat(),
            # Add any other metadata you want to save
        }
        db.collection('images_metadata').document(filename).set(metadata)

        print(f"Image '{filename}' uploaded to Firebase Storage")

def uploadFromFolder():
    # Path to the directory containing images you want to upload
    downloads_dir = "/home/amdt/Desktop/AutoMeteorTracker/image_capture/DSLR"

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
save_location = "/home/amdt/Desktop/AutoMeteorTracker/image_capture/DSLR"

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

if __name__ == '__main__':
    os.chdir(save_location)

    for i in range(0, 20):
        shot_date = datetime.now().strftime("%Y-%m-%d")
        shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        start = time.time()
        captureImages()
        end = time.time()
        print(end - start)
        # sleep(5)
        # renameFiles(picID)

        uploadFromFolder()
