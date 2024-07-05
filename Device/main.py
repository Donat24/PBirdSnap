import logging
import os
import pathlib
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
    path:str

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
    image_filename = os.path.join(config.device.path, "image.jpg")
    try:
        os.remove(image_filename)
    except Exception:
        pass
    
    # make image
    camera.capture_file(image_filename)
    
    # send
    try:
        response = requests.post(
            url=config.api.test_url,
            auth=basic_auth,
            headers=headers,
            files={"image": open(image_filename, "rb")},
            verify=False,
        )
        response.raise_for_status()
    except Exception as e:
        logging.error("unable to upload test-image",exc_info=e)

    # cleanup
    os.remove(image_filename)

    while True:

        camera.capture_file(image_filename)
        logging.info("created new picture")

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

        os.remove(image_filename)
        sleep(config.capture.wait_after_snap)

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
            path=configParser.get("device","path"),
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
    # logging
    logging.basicConfig(level=logging.INFO)
    
    config = pathlib.Path(__file__).parent / "config.ini"
    main(parse_config(str(config)), mog2_frame_analyzer)