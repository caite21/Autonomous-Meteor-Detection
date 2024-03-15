import os
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage




os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "amdt-e236e-firebase-adminsdk-j0x0f-2655e83262.json"

# Initialize Firebase
default_app = firebase_admin.initialize_app()
db = firestore.Client()

def upload_image(filename, local_image_path):
    
    storage_client = storage.Client()
    bucket = storage_client.bucket('amdt-e236e.appspot.com')

    # Name file
    firebase_storage_path = filename
    
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):

        # Create file in the bucket with the desired name
        blob = bucket.blob(firebase_storage_path)

        # Upload the local image file to Firebase Storage
        blob.upload_from_filename(local_image_path)
    



def testupload():
   
    # Path to the directory containing images you want to upload
    downloads_dir = "./"
    
    # Get a list of files in the downloads directory
    files = os.listdir(downloads_dir)
    
    # Iterate through the files
    for file_name in files:
        file_path = os.path.join(downloads_dir, file_name)
        upload_image(file_name, file_path)
        print(f"Image '{file_name}' uploaded to Firebase Storage")
    
    


if __name__ == '__main__':  
    
    # Uploads 6 test images
    testupload()
