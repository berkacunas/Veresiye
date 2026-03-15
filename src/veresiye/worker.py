from pathlib import Path

def process_image_queue(input_path: Path):
    """
    Creates a queue of images from a file or directory and processes them sequentially.
    """
    image_queue = []

    # 1. Build the Queue
    if input_path.is_file():
        image_queue.append(input_path)
    elif input_path.is_dir():
        print(f"Scanning directory: {input_path}")
        # Find all common image formats in the folder
        for ext in ('*.png', '*.jpg', '*.jpeg', '*.tiff'):
            image_queue.extend(input_path.glob(ext))
        
        # Sort alphabetically to process in a predictable order
        image_queue.sort() 
    else:
        print(f"Error: {input_path} is neither a valid file nor a directory.")
        return

    if not image_queue:
        print("No images found to process.")
        return

    print(f"Found {len(image_queue)} image(s). Starting sequential OCR queue...\n")
    print("-" * 40)

    # 2. Process the Queue One by One
    for index, img_path in enumerate(image_queue, start=1):
        print(f"[{index}/{len(image_queue)}] Extracting data from: {img_path.name}")
        
        try:
            # --------------------------------------------------
            # TODO: Your RapidOCR Engine & Pydantic Validation goes here
            # result_data = run_ocr(img_path)
            # validated_data = OCRRow.model_validate(result_data)
            # --------------------------------------------------
            
            print(f"    -> Success!")
            
        except Exception as e:
            print(f"    -> ERROR processing {img_path.name}: {e}")
            # The beauty of the queue: If one image fails, the loop just 
            # catches the error and safely continues to the next image!

    print("-" * 40)
    print("Queue processing complete.")

# Example usage from our argparse setup:
# if args.image_path:
#     process_image_queue(args.image_path)