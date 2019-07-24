#!/usr/bin/python

import os
from datetime import datetime
import time

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


pir.when_motion = motion_detected
pause()


def blob_upload_callback(result, user_context):
    print(str(result))


def motion_detected():
    try:
        # Capture a image on the camera
        filename = os.path.join(PIC_PATH, datetime.now().isoformat())
        jpg_filename = filename + '.jpg'
        camera.capture(jpg_filename)

		# start video recording
        mov_filename = filename + '.h264'
        camera.start_preview()
        camera.start_recording(filename + '.h264')

        # TODO: classify image and determine whether to keep image or not
        keep_image = True
        # TODO adjust message based on classification result
        message = 'Squirrel detected with 0.99 probability'

        # recording duration
        time.sleep(DELAY)

		# stop video recording
        camera.stop_preview()
        camera.stop_recording()

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
