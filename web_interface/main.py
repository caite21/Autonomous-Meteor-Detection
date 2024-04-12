import os
from flask import Flask, render_template, request, redirect, send_file, jsonify
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials
from google.cloud import storage
from datetime import datetime
import requests
from io import BytesIO
import zipfile

# Flask
app = Flask(__name__)

# Initialize Firebase
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "amdt-a1b24-firebase-adminsdk-q32q3-ebfcbcd5a8.json"
default_app = firebase_admin.initialize_app()
db = firestore.Client()

# Firestore document reference
doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")

global zip_this_image_data
global image_data
global images_per_page
images_per_page = 6
global f_start_date
global f_end_date

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/detected_meteors')
def detected_meteors():
    # refresh data
    global zip_this_image_data
    global image_data
    images = get_image_data()
    image_data = images

    images_per_page = 6
    image_data = get_image_data()

    # get only images classified as meteors
    images = [i for i in image_data if i.get('isMeteor') == True]
    total_images = len(images)
    total_pages = (total_images + images_per_page - 1) // images_per_page
    zip_this_image_data = images

    # Get the current page number from the query string
    page = int(request.args.get('page', 1))

    # Calculate start and end indices for the current page
    start = (page - 1) * images_per_page
    end = min(start + images_per_page, total_images)
    # Get images for the current page
    images_on_page = images[start:end]
    return render_template('detected_meteors.html', images=images_on_page, total_pages=total_pages, current_page=page)

from datetime import datetime

@app.route('/all_images')
def all_images():
    # refresh data
    global zip_this_image_data
    global image_data
    images = get_image_data()
    image_data = images


    # filter
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 1, 1)
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        images = [image for image in images if start_date <= datetime.strptime(image['date'][0:10], "%Y-%m-%d") <= end_date]
    except:
        pass

    total_images = len(images)
    total_pages = (total_images + images_per_page - 1) // images_per_page

    global zip_this_image_data
    zip_this_image_data = images

    # Get the current page number from the query string
    page = int(request.args.get('page', 1))

    # Calculate start and end indices for the current page
    start = (page - 1) * images_per_page
    end = min(start + images_per_page, total_images)
    # Get images for the current page
    images_on_page = images[start:end]
    return render_template('all_images.html', images=images_on_page, total_pages=total_pages, current_page=page, filter_start=start_date, filter_end=end_date)



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
    # return render_template('configure.html')


# Flask route for handling form submission
@app.route('/update_run', methods=['POST'])
def update_run():
    if request.method == 'POST':
        data = request.json
        start_time_24h = data['startTime']
        end_time_24h = data['endTime']
        start_day = data['startDay']
        end_day = data['endDay']

        # Reference to the document
        doc_ref = db.collection("sysConfig").document("HvAny5Q1B26cU8PNC1lA")

        # Update Firestore document with start and end times
        doc_ref.update({
            'StartTime': start_time_24h,
            'EndTime': end_time_24h,
            'StartDate': start_day,
            'EndDate': end_day
        })
        return jsonify({'message': 'Run updated successfully'}), 200
    return jsonify({'message': 'Not a POST request'}), 500


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
        # ignore background image for Home page
        # if blob.name.lower() == 'home_background.jpg':
        #     continue

        if blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_url = blob.public_url

            # Retrieve metadata from Firestore
            metadata_ref = db.collection('images_metadata').document(blob.name).get()
            if metadata_ref.exists:
                metadata = metadata_ref.to_dict()
                creation_time = metadata.get('creation_time')
                isMeteor = metadata.get('isMeteor')
            else:
                creation_time = "Unknown"
                isMeteor = False

            # Append image URL and upload date to the list
            image_data.append({'url': image_url, 'date': creation_time, 'isMeteor': isMeteor})

    # sort by most recent
    image_data = sorted(image_data, key=lambda x: x['date'], reverse=True)
    return image_data

@app.route('/download_image/<path:image_path>')
def download_image(image_path):
    # URL of the image to download
    image_url = image_path

    try:
        # Make a GET request to fetch the image data
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an exception for any HTTP error

        # Create a BytesIO object from the response content
        image_data = BytesIO(response.content)

        # Extract the filename from the URL or provide a default filename
        filename = 'AMDT_image.jpg'

        # Set response headers for downloading the image as an attachment
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')
        }

        # Return the image data as a response with headers
        return send_file(image_data, mimetype=response.headers.get('Content-Type'), as_attachment=True, download_name=filename)

    except Exception as e:
        # Handle any errors
        print(f"Error downloading image: {e}")

    # If image download fails, return an error response
    return "Failed to download image.", 500


@app.route('/download_images_as_zip')
def download_images_as_zip():
    try:
        # Create an in-memory zip file
        zip_buffer = BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Download and add each image to the zip file
            for i in zip_this_image_data:
                response = requests.get(i['url'])
                response.raise_for_status()  # Raise an exception for any HTTP error

                classification = i['isMeteor']
                short_date = i['date'].replace(':', '-')
                imagename = f'{classification}_{short_date}.jpg'
                # Add the image data to the zip file
                zip_file.writestr(imagename, response.content)

        # Rewind the buffer to the beginning
        zip_buffer.seek(0)

        # Return the zip file as a Flask response with headers for downloading
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='AMDT_images.zip')

    except Exception as e:
        # Handle any errors
        print(f"Error downloading images: {e}")

    # If image download fails, return an error response
    return "Failed to download images.", 500

if __name__ == '__main__':
    app.run(debug=True)
