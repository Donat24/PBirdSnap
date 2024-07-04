from bird_classifier.bird_v2 import RoboflowBirdV2Classifier
from bird_classifier.classifier import Classifier
from config.config import Config


def create_classifier(config:Config) -> Classifier:
    return RoboflowBirdV2Classifier(
        url=config.roboflow.url,
        key=config.roboflow.key,
        treshold=config.roboflow.treshold,
    )