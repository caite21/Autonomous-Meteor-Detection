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
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Alex/Documents/AMDT/image_capture/DSLR/amdt-a1b24-firebase-adminsdk-q32q3-c9217e3b84.json"

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
    downloads_dir = "C:/Users/Alex/Pictures/Wallpapers"
    
    # Iterate through the files and upload
    files = os.listdir(downloads_dir)
    for file_name in files:
        file_path = os.path.join(downloads_dir, file_name)
        upload_image(file_name, file_path)



if __name__ == '__main__':
    
    uploadFromFolder()
    
    """
    for i in range(0,50):
        uploadFromFolder()
        time.sleep(10)
    """
