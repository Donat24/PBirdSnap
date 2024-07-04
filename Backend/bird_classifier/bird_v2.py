
from pathlib import Path
from typing import List, override

from inference_sdk import InferenceHTTPClient

from bird_classifier.classifier import Classifier, ClassifierError


class RoboflowBirdV2Classifier(Classifier):
    def __init__(self, url:str, key:str, treshold:float=0.15) -> None:
        self.client = InferenceHTTPClient(
            api_url=url,
            api_key=key,
        ).select_model("bird-v2/2")
        self.treshold = treshold

    @override
    def classifiy(self, storage_path:Path) -> List[str]:
        try:
            result = self.client.infer(str(storage_path))
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
                     