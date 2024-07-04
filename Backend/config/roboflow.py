from dataclasses import dataclass


@dataclass
class RoboflowConfig:
    url:str
    key:str
    treshold:float
