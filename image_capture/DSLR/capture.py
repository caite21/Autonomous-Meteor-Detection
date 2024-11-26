""" 
    gPhoto functions for the Autonomous Meteor Detection System
"""

from time import sleep
from datetime import datetime
from sh import gphoto2 as gp
import time
import os
import signal
import subprocess


clearCommand = ["--folder", "/store_00020001/DCIM/100CANON", "--delete-all-files", "-R"]
triggerCommand = ["--capture-image-and-download"]

def kill_gphoto():
    """ Kill the gphoto process that starts whenever we turn on the 
    camera or "reboot the raspberry pi """

    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()

    # Search for the process we want to kill
    for line in out.splitlines():
        if b'gvfsd-gphoto2' in line:
            # Kill that process!
            pid = int(line.split(None,1)[0])
            os.kill(pid, signal.SIGKILL)


def trigger_capture():
    gp(triggerCommand)

