import logging
import os
from configparser import ConfigParser
from dataclasses import dataclass
from time import sleep
from typing import Callable

import cv2
import numpy as np
import picamera2
import requests
from requests.auth import HTTPBasicAuth


@dataclass
class ApiConfig:
    test_url: str
    upload_url: str
    user:str
    password:str
    key:str

@dataclass
class CaptureConfig:
    pixel_x:int
    pixel_y:int
    wait_after_snap:float

@dataclass
class DeviceConfig:
    id:str

@dataclass
class Config:
    device:DeviceConfig
    api:ApiConfig
    capture:CaptureConfig


def main(config:Config, frame_analyzer:Callable[[str], bool]):
    
    basic_auth = HTTPBasicAuth(config.api.user, config.api.password)
    headers={
        r"device-id": config.device.id,
        r"X-API-KEY" : config.api.key
    }

    camera = picamera2.Picamera2()

    preview_config = camera.create_preview_configuration(
        main={"size": (config.capture.pixel_x, config.capture.pixel_y)}
    )
    camera.configure(preview_config)
    camera.start()
    sleep(2)

    # test image
    test_image_filename = "test_image.jpg"
    try:
        os.remove(test_image_filename)
    except Exception:
        pass
    
    camera.capture_file(test_image_filename)
    
    try:
        response = requests.post(
            url=config.api.test_url,
            auth=basic_auth,
            headers=headers,
            files={"image": open(test_image_filename, "rb")},
            verify=False,
        )
        response.raise_for_status()
    except Exception as e:
        logging.error("unable to upload test-image",exc_info=e)


    # do birdsnaps
    image_filename = "image.jpg"
    while True:
        camera.capture_file(image_filename)
        logging.info("creatd new picture")

        if frame_analyzer(image_filename):
            try:
                logging.info("new birdsnap created")
                response = requests.post(
                    url=config.api.upload_url,
                    auth=basic_auth,
                    headers=headers,
                    files={"image": open(image_filename, "rb")},
                    verify=False,
                )
                response.raise_for_status()
            except Exception as e:
                logging.error("unable to upload test-image", exc_info=e)


        sleep(config.capture.wait_after_snap)
        os.remove(image_filename)

fgbg = cv2.createBackgroundSubtractorMOG2()
def mog2_frame_analyzer(filename:str):
    frame = cv2.imread(filename, cv2.IMREAD_COLOR)
    frame = cv2.medianBlur(frame, 7)
    frame = fgbg.apply(frame)
    frame = cv2.medianBlur(frame, 7)
    frame[frame < 0.5] = 0
    return np.sum(frame / 255) > 80
    

def parse_config(filepath:str) -> Config:
    configParser = ConfigParser()
    configParser.read(filepath)
    return Config(
        device=DeviceConfig(
            id=configParser.get("device","id"),
        ),
        api=ApiConfig(
            test_url=configParser.get("api","test_url"),
            upload_url=configParser.get("api","upload_url"),
            user=configParser.get("api","user"),
            password=configParser.get("api","password"),
            key=configParser.get("api","key"),
        ),
        capture=CaptureConfig(
            pixel_x=configParser.getint("capture","pixel_x"),
            pixel_y=configParser.getint("capture","pixel_y"),
            wait_after_snap=configParser.getfloat("capture","wait_after_snap"),
        )
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(parse_config("config.ini"), mog2_frame_analyzer)