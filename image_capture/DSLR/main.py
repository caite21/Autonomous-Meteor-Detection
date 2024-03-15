from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import time
import signal, os, subprocess

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
	
	for i in range(0,20):
	    shot_date = datetime.now().strftime("%Y-%m-%d")
	    shot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	    start = time.time()
	    captureImages()
	    end = time.time()
	    print(end - start)
	    #sleep(5)
	    #renameFiles(picID)

