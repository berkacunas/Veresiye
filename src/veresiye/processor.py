import json
from pathlib import Path

from veresiye.models import ParsedReceipt
from veresiye.parsers import MigrosParser, YildizKuruyemisParser, GenericParser

class ReceiptProcessor:
    
    def __init__(self):
        
        self.chain = [MigrosParser(), YildizKuruyemisParser(), GenericParser()]

    def process(self, ocr_lines: list, shop_name: str = 'Unknown', output_path: Path = Path("results.jsonl")) -> bool:
        
        for parser in self.chain:
            result = parser.parse(ocr_lines)
            if result:
                return self._write_to_jsonl(result, output_path)
        
        print(f"Warning: The {shop_name} receipt could not be read by any parser in the chain!")
        
        # Test amaçlı: Parser olmadan doğrudan yazdırıyoruz
        return False
    
    
    def _write_to_jsonl(self, receipt_data: ParsedReceipt, output_path: Path):
        """
        Appends the incoming Pydantic objects (.jsonl) to the file as a single line.
        """
        payload = receipt_data.model_dump()
        
        # Open the file in "Append" mode and type the line: 
        # # ensure_ascii=False -> Prevents corruption of Turkish characters (e.g., Ş, Ğ, Ç)
        with open(output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            
        print(f"    -> [SAVED] Data {receipt_data.market} has been added to the {receipt_data.total_amount} file.")
        return True
