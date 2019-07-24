#!/usr/bin/python

import os
from datetime import datetime
import time
import requests
import json

from gpiozero import MotionSensor
from signal import pause
from picamera import PiCamera
from iothub_client import IoTHubClient, IoTHubTransportProvider

from NotifcationHubClient import NotificationHub

DEBUG = 0

# setup picture folder
PIC_PATH = os.environ['LOCAL_PICTURE_PATH']
os.makedirs(PIC_PATH, exist_ok=True)

# setup Motion Sensor
pir = MotionSensor(11)

# number of seconds to delay between alarms
DELAY = 10

# instatiate the Pi Camera
camera = PiCamera()

# setup iothub client
iot_client = IoTHubClient(os.environ['IOTHUB_CONNECTION_STRING'], IoTHubTransportProvider.HTTP)

# setup notificationhub client
nh_client = NotificationHub(connection_string=os.environ['NH_CONNECTION_STRING'], 
                            hub_name=os.environ['NH_NAME'],
                            debug=DEBUG)

IMAGE_PROCESSING_ENDPOINT = os.getenv('IMAGE_PROCESSING_ENDPOINT', "http://wildlife-image-classifier:80/image")
VERBOSE=  os.getenv('VERBOSE', False)
THRESHOLD = 0.7

def blob_upload_callback(result, user_context):
    print(str(result))


def send_frame_for_processing(imagePath):
    files = {'imageData': open(imagePath, 'rb').read()}
    try:
        response = requests.post(IMAGE_PROCESSING_ENDPOINT, files=files)
    except Exception as e:
        print('sendFrameForProcessing Excpetion -' + str(e))
        return "[]"
    if VERBOSE:
        try:
            print("Response from external processing service: (" + str(response.status_code) + ") " + json.dumps(response.json()))
        except Exception:
            print("Response from external processing service (status code): " + str(response.status_code))
    return response


def motion_detected():
    try:
        # Capture a image on the camera
        filename = os.path.join(PIC_PATH, datetime.now().isoformat())
        jpg_filename = filename + '.jpg'
        camera.capture(jpg_filename)

		# start video recording
        mov_filename = filename + '.h264'
        camera.start_preview()
        camera.start_recording(mov_filename)

        # call image classifier
        response = send_frame_for_processing(filename)
        predictions = response.json()["predictions"]
        image_object = sorted(predictions, key = lambda i: i['probability'])[0]

        # recording duration
        time.sleep(DELAY)
        
        camera.stop_preview()
        camera.stop_recording()

        # TODO: classify image and determine whether to keep image or not
        keep_image = False
        if image_object["probability"] > THRESHOLD:
            keep_image = True
        
        # TODO adjust message based on classification result
        message = '{} detected with {} probability'.format(image_object["tagName"],image_object["probability"])
        
        if keep_image:
            # print and push message
            # TODO: change message to include classifcation result
            print(message)
            nh_client.send_fcm_notification(payload=dict(data=dict(message=message)))

            # send picture to blob
            with open(jpg_filename, 'rb') as f:
                content = f.read()
                iot_client.upload_blob_async(jpg_filename, content, len(content), blob_upload_callback, DEBUG)

            # send movie recording to blob
            with open(mov_filename, 'rb') as f:
                content = f.read()
                iot_client.upload_blob_async(jpg_filename, content, len(content), blob_upload_callback, DEBUG)
        else:
            # clear out image and recording
            os.remove(jpg_filename)
            os.remove(mov_filename)
    
    except Exception as e:
        print('Encountered exception: {}\n Carrying on...'.format(e))

    finally:
        # stop video recording
        camera.stop_preview()
        camera.stop_recording()


pir.when_motion = motion_detected
pause()