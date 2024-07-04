
import base64
from pathlib import Path
from typing import List, override
from urllib.parse import urljoin

import requests

from bird_classifier.classifier import Classifier, ClassifierError


class RoboflowBirdV2Classifier(Classifier):
    def __init__(self, url:str, key:str, treshold:float=0.15) -> None:
        self.model_url = urljoin(url, "bird-v2/2")
        self.key = key
        self.treshold = treshold
    
    def _create_request(self, data:bytes):
        data = base64.b64encode(data)
        params = {"api_key": self.key}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(self.model_url, params=params, data=data, headers=headers)
        return response

    @override
    def classifiy(self, storage_path:Path) -> List[str]:

        with open(storage_path, "rb") as image_file:
            data = image_file.read()
        
        try:
            response = self._create_request(data)
            response.raise_for_status()
            result = response.json()

        except Exception as e:
            raise ClassifierError() from e
        
        if not "predictions" in result.keys():
            raise ClassifierError()
        
        predictions = list(map(
            lambda prediction: prediction["class"],
            filter(
                lambda prediction: float(prediction["confidence"]) > self.treshold,
                result["predictions"]
            )
        ))

        return predictions
                     