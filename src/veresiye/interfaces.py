from abc import ABC, abstractmethod

class ReceiptParserInterface(ABC):
    
    @abstractmethod
    def parse(self, ocr_lines):
        pass
