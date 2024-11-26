""" 
    Functions to find and connect Raspberry Pi to Wi-Fi for the 
    Autonomous Meteor Detection System
"""

import warnings
import requests
import subprocess


def what_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'ACTIVE,SSID', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split(':')[1]
    else:
        return ''

def is_connected_to(ssid: str):
    return what_wifi() == ssid

def scan_wifi():
    process = subprocess.run(['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi'], stdout=subprocess.PIPE)
    if process.returncode == 0:
        return process.stdout.decode('utf-8').strip().split('\n')
    else:
        return []
        
def is_wifi_available(ssid: str):
    return ssid in [x.split(':')[0] for x in scan_wifi()]

def wait_for_wifi():
    ssid = "test"
    password = 'key'
    while not is_wifi_available(ssid):
        pass
    if not is_connected_to(ssid):
        print("Wi-Fi found, trying to connect")
        subprocess.call(['nmcli', 'd', 'wifi', 'connect', ssid, 'password', password])

def test_internet():
    try:
        res = requests.get("https://console.firebase.google.com/u/2/project/amdt-a1b24")
        return True
    except requests.ConnectionError:
        return False