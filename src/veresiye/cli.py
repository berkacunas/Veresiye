import argparse
import sys
from pathlib import Path

from veresiye.processor import ReceiptProcessor
from veresiye.scanner import scan_image, scan_image_queue

def setup_argparse() -> argparse.ArgumentParser:
    
    parser = argparse.ArgumentParser(
        prog="Veresiye OCR",
        description="Extract and validate text from receipts and invoices.",
        epilog="Example: python cli.py receipt.jpg --output result.json --min-confidence 0.90 --headless"
    )

    parser.add_argument(
        "image_path",
        type=Path, # Automatically converts input to a Pathlib object
        nargs="?", # Makes it optional so the GUI can still launch if no image is provided
        help="Path to the image file to be processed."
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        metavar="FILE",
        help="Path to save the extracted data (e.g., output.json). Prints to console if omitted."
    )

    parser.add_argument(
        "-c", "--min-confidence",
        type=float,
        default=0.0,
        metavar="FLOAT",
        help="Minimum confidence score threshold (0.0 to 1.0). Default is 0.0."
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run OCR in the background without launching the PySide6 GUI."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed logging output."
    )

    return parser

def main():
    
    parser = setup_argparse()
    args = parser.parse_args()

    processor = ReceiptProcessor()
    
    if args.image_path and args.headless:
        print(f"Running in HEADLESS mode processing: {args.image_path}")
        
        if args.verbose:
            print(f"Minimum confidence set to: {args.min_confidence}")
            if args.output:
                print(f"[-] Çıktı dosyası: {args.output}")
                
        image_path = args.image_path
        
        # Capture the pair (file_path, ocr_data) returned from the generator.
        for img_path, ocr_lines in scan_image_queue(image_path):
            
            # Filter Pydantic models based on their confidence score.
            confident_lines = [line for line in ocr_lines 
                               if line.confidence >= args.min_confidence]
        
            if not confident_lines:
                if args.verbose:
                    print(f"    > [SKIPPED] {img_path.name}: No text found that passed the security threshold.")
                continue
        
            output_file = args.output if args.output else Path("results.jsonl")
            processor.process(confident_lines, shop_name=img_path.stem, output_path=output_file)
        
        print("[*] Headless işlem kuyruğu tamamlandı.")
        
    elif args.image_path:
        print(f"Launching GUI and pre-loading image: {args.image_path}")
        print("    (Note: The UI module is currently closed for core development.)")
        # TODO: app = QApplication(sys.argv)
        # TODO: window = MainWindow(initial_image=args.image_path)
        # TODO: window.show()
        # TODO: sys.exit(app.exec())
        
    else:
        print("Launching standard GUI...")
        print("    (Note: The UI module is currently closed for core development.)")
        # TODO: app = QApplication(sys.argv)
        # TODO: window = MainWindow()
        # TODO: window.show()
        # TODO: sys.exit(app.exec())

if __name__ == "__main__":
    main()
    