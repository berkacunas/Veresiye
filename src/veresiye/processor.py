# 3. Chain of Responsibility (Zincir Yöneticisi)
class ReceiptProcessor:
    def __init__(self):
        # Zinciri en olasıdan/en spesifik olandan en genele doğru diziyoruz
        self.chain = [MigrosParser(), YildizKuruyemisParser(), GenericParser()]

    def process(self, shop_name, ocr_data):
        for parser in self.chain:
            # İlgili dükkanın parser'ını bul veya doğrudan hepsini dene
            result = parser.parse(ocr_data)
            if result:
                return self._write_to_jsonl(result)
        
        print(f"Uyarı: {shop_name} fişi zincirdeki hiçbir parser tarafından okunamadı!")
        return None

    def _write_to_jsonl(self, data):
        # JSONL dosyasına append (ekleme) işlemi
        pass