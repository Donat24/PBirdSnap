
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List


class ClassifierError(Exception):
    pass

class Classifier(ABC):
    @abstractmethod
    def classifiy(self, storage_path:Path) -> List[str]:
        raise NotImplementedError()
    
    def __call__(self, storage_path:Path) -> List[str]:
        return self.classifiy(storage_path)
            