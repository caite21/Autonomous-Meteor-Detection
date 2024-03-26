import os
from flask import Flask, render_template, request, redirect
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage

# Flask
app = Flask(__name__)

# Initialize Firebase
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Alex/Documents/AMDT/image_capture/DSLR/amdt-a1b24-firebase-adminsdk-q32q3-c9217e3b84.json"
default_app = firebase_admin.initialize_app()
db = firestore.Client()

# Firestore document reference
doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")

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
    start_date, start_time, end_date, end_time = read_sys_config()
    return render_template('configure.html', start_date=start_date, start_time=start_time, end_date=end_date, end_time=end_time)
    #return render_template('configure.html')
                           
# Flask route for handling form submission
@app.route('/update_run', methods=['POST'])
def update_run():
    if request.method == 'POST':
        data = request.json
        start_time = data['startTime']
        end_time = data['endTime']
        start_day = data['startDay']
        end_day = data['endDay']

        # Reference to the document
        doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")

        # Update Firestore document with start and end times
        doc_ref.update({
            'StartTime': start_time,
            'EndTime': end_time,
            'StartDate': start_day,
            'EndDate': end_day
        })
        


def read_sys_config():
    # Reference to the document
    doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")
    
    # Retrieve the document snapshot
    doc = doc_ref.get()
    
    if doc.exists:
        # Get data from the document
        data = doc.to_dict()
        
        end_date_str = data.get("EndDate")
        end_time_str = data.get("EndTime")
        start_date_str = data.get("StartDate")
        start_time_str = data.get("StartTime")   
        
        return start_date_str, start_time_str, end_date_str, end_time_str
    else:
        print("Document does not exist")
        return None, None, None, None


def get_image_data():
    storage_client = storage.Client()
    bucket = storage_client.bucket('amdt-a1b24.appspot.com')

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
    app.run(debug=True)
