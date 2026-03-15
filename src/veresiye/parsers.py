import re

from veresiye.interfaces import ReceiptParserInterface
from veresiye.models import ParsedReceipt, ReceiptItem

class MigrosParser(ReceiptParserInterface):

    
    date_pattern = re.compile(r"TARIH:(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
    time_pattern = re.compile(r"SAAT:(\d{2}:\d{2})", re.IGNORECASE)
    receipt_no_pattern = re.compile(r"FIS NO:(\d+)", re.IGNORECASE)
    total_pattern = re.compile(r"^TOPLAM\s*[*xX]\s*([\d.,]+)", re.IGNORECASE)
    
    # Product Regex Patterns
    # ######################
    # Multiplier (Quantity/Unit) Memory: Example "4 PCS × 26.75 TL/PCS"
    # [*xX×] part protects against OCR reading the cross symbol as x, X, *, or an actual cross (×).
    multiplier_pattern = re.compile(r"(\d+)\s*AD\s*[*xX×]\s*([\d.,]+)\s*TL/AD", re.IGNORECASE)
    
    # Product Line: Ex "ULKER CIKOLT.GOFRET %1 x17,95"
    # Group 1: Product Name | Group 2: VAT Rate | Group 3: Total Price
    product_pattern = re.compile(r"^(.*?)\s+%(\d{1,2})\s*[*xX×]\s*([\d.,]+)$", re.IGNORECASE)

    def parse(self, ocr_lines) -> ParsedReceipt | None:

        # It processes the incoming OCRLine list and returns a ParsedReceipt object if successful.
        text_lines = [line.text for line in ocr_lines]
        
        # Verify Identity. Required for Chain of Responsibility pattern
        # If "MIGROS" does not appear in the first 3 lines of the receipt, 
        # reject the receipt, stating that it is not my responsibility.
        if not any("MIGROS" in text.upper() for text in text_lines[:3]):
            return None
        
        receipt = ParsedReceipt(market="Migros")
        
        
        # State Variables
        # If any multiplier exists in a row, temporarily keep them here.
        temp_quantity = 1.0
        temp_unit_price = 0.0
        
        for text in text_lines:
            
            # Metadata
            if match := self.date_pattern.search(text):
                receipt.date = match.group(1)
                continue
                
            elif match := self.time_pattern.search(text):
                receipt.hour = match.group(1)
                continue
                
            elif match := self.receipt_no_pattern.search(text):
                receipt.receipt_no = match.group(1)
                continue
                
            elif match := self.total_pattern.search(text):
                receipt.total_amount = float(match.group(1).replace(",", "."))
                continue
            
            # Product Multiplier Control (Save to Memory)
            if match := self.multiplier_pattern.search(text):
                temp_quantity = float(match.group(1))
                temp_unit_price = float(match.group(2).replace(",", "."))
                continue
            
            # Product Line Control
            if match := self.product_pattern.search(text):
                name = match.group(1).strip()
                tax_rate = f"%{match.group(2)}"
                total_price = float(match.group(3).replace(",", "."))
                
                # If no multiplier is already stored in memory, 
                # the unit price is equal to the total price.
                if temp_quantity == 1.0:
                    unit_price = total_price
                else:
                    unit_price = temp_unit_price

                # Create the object
                item = ReceiptItem(name=name, quantity=temp_quantity, unit_price=unit_price, total_price=total_price, tax_rate=tax_rate)
                receipt.products.append(item)
                
                # After adding the product to the list, reset the memory for the next product!
                temp_quantity = 1.0
                temp_unit_price = 0.0

        return receipt
        
        # Migros's custom abbreviation dictionary and logic
        # mapping = {"ULKER POTIBOR": "Ülker Pötibör"} 

class YildizKuruyemisParser(ReceiptParserInterface):
    
    def parse(self, ocr_data):
        pass
    
class GenericParser(ReceiptParserInterface):
    
    # Flexible dates: 15/03/2026, 15.03.2026, 15-03-2026
    date_pattern = re.compile(r"(\d{2}[/.-]\d{2}[/.-]\d{4})")
    time_pattern = re.compile(r"(\d{2}:\d{2}(?::\d{2})?)")
    # Flexible template for receipt number (Receipt, Invoice, Document)
    receipt_no_pattern = re.compile(r"(?:F[Iİ]S|BELGE)\s*NO[:\s]*(\d+)", re.IGNORECASE)
    # Fractional numbers next to words like Total, Amount, Credit Card, Cash
    total_pattern_inline = re.compile(r"(?:TOPLAM|TUTAR|NAK[Iİ]T|K\.?KARTI)\s*[:*xX\-]?\s*([\d]+[.,]\d{2})", re.IGNORECASE)
    # A solitary, orphaned price pattern that may be preceded by strange OCR characters (*, ￥).
    floating_price_pattern = re.compile(r"^[*xX×￥₺$€]?\s*(\d+[.,]\d{2})$")

    def parse(self, ocr_lines) -> ParsedReceipt | None:
        
        text_lines = [line.text.strip() for line in ocr_lines if line.text.strip()]
        
        if not text_lines:
            return None

        guessed_market = "Bilinmeyen Market"
        for text in text_lines[:5]:
            if "HOSGELD" not in text.upper() and "TESEKKUR" not in text.upper():
                guessed_market = text[:30]
                break

        receipt = ParsedReceipt(market=guessed_market)
        possible_totals = []

        # Line-by-line scanning
        for text in text_lines:
            # Date
            if not receipt.date and (match := self.date_pattern.search(text)):
                # We convert periods or dashes to the standard slash (/) symbol.
                receipt.date = match.group(1).replace(".", "/").replace("-", "/")
            
            # Hour
            if not receipt.hour and (match := self.time_pattern.search(text)):
                receipt.hour = match.group(1)[:5]   # If there are seconds, get only HH:MM
                
            # Receipt No
            if not receipt.receipt_no and (match := self.receipt_no_pattern.search(text)):
                receipt.receipt_no = match.group(1)

            if match := self.total_pattern_inline.search(text):
                try: 
                    possible_totals.append(float(match.group(1).replace(",", ".")))
                except ValueError: 
                    pass

            elif match := self.floating_price_pattern.search(text):
                try: 
                    possible_totals.append(float(match.group(1).replace(",", ".")))
                except ValueError: 
                    pass
                
        if possible_totals:
            receipt.total_amount = max(possible_totals)

        return receipt
