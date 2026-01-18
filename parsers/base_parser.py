from abc import ABC, abstractmethod
from pathlib import Path

class IParser(ABC):
    @abstractmethod
    def parse(self, pdf_path: Path, is_manual: bool = False):
        pass