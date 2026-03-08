# 2. Dükkanlara Özel Sınıflar
class MigrosParser(ReceiptParserInterface):
    def parse(self, ocr_data):
        # Migros'a özel kısaltma sözlüğü ve mantığı
        # mapping = {"ULKER POTIBOR": "Ülker Pötibör"}
        # Başarılıysa JSONL satırı döner, başarısızsa None döner.
        pass

class YildizKuruyemisParser(ReceiptParserInterface):
    def parse(self, ocr_data):
        # T.GIDA anomalisini çözen mantık
        pass
