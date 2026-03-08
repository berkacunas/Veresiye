from veresiye.parsers import MigrosParser, YildizKuruyemisParser, GenericParser

class ReceiptProcessor:
    def __init__(self):
        
        self.chain = [MigrosParser(), YildizKuruyemisParser(), GenericParser()]

    def process(self, shop_name, ocr_data):
        
        for parser in self.chain:
            result = parser.parse(ocr_data)
            if result:
                return self._write_to_jsonl(result)
        
        print(f"Warning: The {shop_name} receipt could not be read by any parser in the chain!")
        return None

    def _write_to_jsonl(self, data):
        # append to JSONLs
        pass