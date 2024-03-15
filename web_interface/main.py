import os
from flask import Flask, render_template, request
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage


# Flask
###########################################################################################
app = Flask(__name__)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/detected_meteors')
def detected_meteors():
    # Fetch detected meteors from Firestore
    meteors_ref = db.collection('meteors').get()
    meteors = [meteor.to_dict() for meteor in meteors_ref]
    return render_template('detected_meteors.html', meteors=meteors)

@app.route('/all_images')
def all_images():
    # Fetch image data including URLs and dates from Firebase Storage
    image_data = get_image_data()
    return render_template('all_images.html', images=image_data)

@app.route('/live_stream')
def live_stream():
    return render_template('live_stream.html')

@app.route('/diagnostics')
def diagnostics():
    return render_template('diagnostics.html')

@app.route('/configure')
def configure():
    return render_template('configure.html')
###########################################################################################



# TODO Change so key is not hardcoded
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Alex/Documents/AutoMeteorTracker/web_interface/amdt-e236e-firebase-adminsdk-j0x0f-2655e83262.json"

# Initialize Firebase
default_app = firebase_admin.initialize_app()
db = firestore.Client()



def get_image_data():
    storage_client = storage.Client()
    bucket = storage_client.bucket('amdt-e236e.appspot.com')

    # List all the files in the bucket
    blobs = bucket.list_blobs()

    # Get URLs and dates of images in the bucket
    image_data = []
    for blob in blobs:
        if blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_url = blob.public_url

            # Retrieve metadata from Firestore
            metadata_ref = db.collection('images_metadata').document(blob.name).get()
            if metadata_ref.exists:
                metadata = metadata_ref.to_dict()
                creation_time = metadata.get('creation_time')
            else:
                upload_time_str = "Unknown"

            # Append image URL and upload date to the list
            image_data.append({'url': image_url, 'date': creation_time})

    return image_data
  
    

if __name__ == '__main__':  
    
    #Run Flask
    app.run(debug=True)
    
    
    
    
    
    
