from abc import ABC, abstractmethod

# 1. Sözleşmemiz (Interface)
class ReceiptParserInterface(ABC):
    @abstractmethod
    def parse(self, ocr_data):
        pass


