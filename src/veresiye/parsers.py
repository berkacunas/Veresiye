from veresiye.interfaces import ReceiptParserInterface

class MigrosParser(ReceiptParserInterface):

    def parse(self, ocr_data):
       # Migros's custom abbreviation dictionary and logic
        # mapping = {"ULKER POTIBOR": "Ülker Pötibör"} 
        # # Returns JSONL line if successful, None if unsuccessful.
        pass

class YildizKuruyemisParser(ReceiptParserInterface):
    
    def parse(self, ocr_data):
        pass
