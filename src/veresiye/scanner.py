import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, ValidationError
from rapidocr_onnxruntime import RapidOCR

# Pydantic Models
class OCRWord(BaseModel):
    """Verified model of individual word/block fragments from RapidOCR."""
    box: List[List[float]] # 4 adet [x, y] koordinat çifti olmak zorunda
    text: str
    confidence: float = Field(ge=0.0, le=1.0) # Skor kesinlikle 0 ile 1 arasında olacak!
    x_left: float
    y_center: float

class OCRLine(BaseModel):
    """Clustered and combined final row model."""
    box: List[List[float]]
    text: str
    confidence: float = Field(ge=0.0, le=1.0)

def _extract_spatial_features(item: list) -> dict:
    """
    Retrieves the raw list, checks for missing items, and returns a safe Pydantic object.
    """
    # Guard clause: Ensure item has text and a valid 4-point bounding box
    if not isinstance(item, list) or len(item) < 3:
        raise ValueError(f"Malformed OCR item detected: {item}")

    box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text = str(item[1])
    confidence = float(item[2])
    
    if not box or len(box) < 4:
        raise ValueError(f"Faulty coordinate box: {box}")
    
    # Calculate the vertical center and left starting point
    y_center = (box[0][1] + box[2][1]) / 2.0
    x_left = box[0][0]
    
    #  Submit the data to Pydantic. If there are any errors, it will throw a ValidationError
    return OCRWord(box=box, text=text, confidence=confidence, x_left=x_left, y_center=y_center)

def _cluster_items_by_line(spatial_items: list, y_tolerance: int) -> list:
    """
    Cluster Pydantic objects (OCRWord) according to y-center
    """
    lines = []
    for item in spatial_items:
        found_line = False
        for line in lines:
            # If the item's Y-center is close to the line's Y-center, they belong together
            if abs(line['y_center'] - item.y_center) < y_tolerance:
                line['items'].append(item)
                # Update the running average of the line's Y-center
                line['y_center'] = (line['y_center'] + item.y_center) / 2.0
                found_line = True
                break
                
        # Create a new line cluster if no match is found
        if not found_line:
            lines.append({'y_center': item.y_center, 'items': [item]})
            
    return lines

def _sort_and_format_lines(lines: list) -> List[OCRLine]:
    """
    Task: Sorts the clustered lines top-to-bottom, and items left-to-right, then joins them.
    """
    # Sort lines vertically (top to bottom)
    lines.sort(key=lambda l: l['y_center'])
    structured_data = []
    
    for line in lines:
        items: List[OCRWord] = line['items']
        
        # Sort objects from left to right according to the x_left value
        items.sort(key=lambda i: i.x_left)
        
        joined_text = " ".join([i.text for i in items])
        avg_confidence = sum(i.confidence for i in items) / len(items)
        
        first_box = items[0].box
        last_box = items[-1].box
        
        merged_box = [
            first_box[0],  # Top Left of the first word
            last_box[1],   # The last word is in the top right corner.
            last_box[2],   # The last word is Bottom Right
            first_box[3]   # Bottom Left of the first word
        ]
        
        try:
            ocr_line = OCRLine(box=merged_box, text=joined_text, confidence=avg_confidence)
            structured_data.append(ocr_line)
        except ValidationError as e:
            print(f"[UYARI] Pydantic satır doğrulamasını geçemedi, atlanıyor: {joined_text}")
            print(e)
            
    return structured_data

def process_document_layout(ocr_results: list, y_tolerance: int = 15) -> List[OCRLine]:
    """
    Main Director: Manages end-to-end layout analysis with Pydantic models.
    """
    spatial_items = []
    
    for item in ocr_results:
        
        try:
            valid_word = _extract_spatial_features(item)
            spatial_items.append(valid_word)
            
        except (ValueError, ValidationError) as e:
            print(f"[ATLANDI] Faulty word data: {e}")
            continue # Skip the error, don't crush
            
    if not spatial_items:
        return []
    
    clustered_lines = _cluster_items_by_line(spatial_items, y_tolerance)
    final_lines = _sort_and_format_lines(clustered_lines)
    
    return final_lines

def get_raw_ocr_results(image_path: str) -> list:
    """Returns the raw OCR bounding boxes and text without formatting."""
    if not os.path.exists(image_path):
        return []
        
    ocr_engine = RapidOCR()
    results, _ = ocr_engine(image_path)
    
    return results

def scan_image(image_path: str) -> List[OCRLine]:
    """
    Initializes the RapidOCR engine (ONNX based) and tests it on a given receipt image.
    """
    print("[SYSTEM] Initializing RapidOCR (ONNX Runtime)...")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return
    
    ocr_engine = RapidOCR()
    
    print(f"[SYSTEM] Processing image: {image_path}")
    results, elapse = ocr_engine(image_path)
    
    if not results:
        print("[WARNING] No text could be extracted from the image.")
        return

    ocr_lines: List[OCRLine] = process_document_layout(results)
    
    print(f"[SYSTEM] Extraction completed in {elapse} seconds.")
    print("-" * 50)
    
    for line in ocr_lines:
        print(f"Metin: {line.text:<30} | Güven Skoru: {line.confidence*100:.2f}%")
    
    print("-" * 50)
    
    return ocr_lines

def scan_image_queue(input_path: Path):
    """
    Creates a queue of images from a file or directory and processes them sequentially.
    """
    image_queue = []
    if input_path.is_file():
        image_queue.append(input_path)
        
    elif input_path.is_dir():
        print(f"Scanning directory: {input_path}")
        
        # Find all common image formats in the folder
        for ext in ('*.png', '*.jpg', '*.jpeg', '*.tiff'):
            image_queue.extend(input_path.glob(ext))
        
        image_queue.sort() 
        
    else:
        print(f"Error: {input_path} is neither a valid file nor a directory.")
        return

    if not image_queue:
        print("No images found to process.")
        return

    print(f"Found {len(image_queue)} image(s). Starting sequential OCR queue...\n")
    print("-" * 40)

    for index, img_path in enumerate(image_queue, start=1):
        print(f"[{index}/{len(image_queue)}] Extracting data from: {img_path.name}")
        
        try:
            ocr_lines = scan_image(img_path)
            print(f"    -> Success!")
            
            yield img_path, ocr_lines
            
        except Exception as e:
            print(f"    -> ERROR processing {img_path.name}: {e}")
            # If one image fails, the loop just catches the error and safely continues to the next image

    print("-" * 40)
    print("Queue processing complete.")
