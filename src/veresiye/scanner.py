import os
from rapidocr_onnxruntime import RapidOCR

def _extract_spatial_features(item: list) -> dict:
    """
    Task: Extracts only the required spatial data (Y-center, X-left) from a raw OCR item.
    """
    # Guard clause: Ensure item has text and a valid 4-point bounding box
    if not item or len(item) < 2 or not item[0] or len(item[0]) < 4:
        raise ValueError(f"Malformed OCR item detected: {item}")

    box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text = item[1]
    confidence = item[2]
    
    # Calculate the vertical center and left starting point
    y_center = (box[0][1] + box[2][1]) / 2
    x_left = box[0][0]
    
    return { "text": text, "x_left": x_left, "y_center": y_center, "box": box, "confidence": confidence }

def _cluster_items_by_line(spatial_items: list, y_tolerance: int) -> list:
    """
    Task: Groups independent text items into logical lines based on vertical proximity.
    """
    lines = []
    for item in spatial_items:
        found_line = False
        for line in lines:
            # If the item's Y-center is close to the line's Y-center, they belong together
            if abs(line['y_center'] - item['y_center']) < y_tolerance:
                line['items'].append(item)
                # Update the running average of the line's Y-center
                line['y_center'] = (line['y_center'] + item['y_center']) / 2
                found_line = True
                break
                
        # Create a new line cluster if no match is found
        if not found_line:
            lines.append({
                'y_center': item['y_center'],
                'items': [item]
            })
    return lines

def _sort_and_format_lines(lines: list) -> list:
    """
    Task: Sorts the clustered lines top-to-bottom, and items left-to-right, then joins them.
    """
    # Sort lines vertically (top to bottom)
    lines.sort(key=lambda l: l['y_center'])
    structured_data = []
    
    for line in lines:
        # Sort items horizontally (left to right) within the line
        line['items'].sort(key=lambda i: i['x_left'])
        
        # Join the sorted items into a single string
        joined_text = " ".join([i['text'] for i in line['items']])
        
        # Calculate average confidence for the line
        avg_confidence = sum(i['confidence'] for i in line['items']) / len(line['items'])
        
        # Create a master bounding box for the whole line
        first_item_box = line['items'][0]['box']
        last_item_box = line['items'][-1]['box']
        
        merged_box = [
            first_item_box[0], # Top-Left of the first word
            last_item_box[1],  # Top-Right of the last word
            last_item_box[2],  # Bottom-Right of the last word
            first_item_box[3]  # Bottom-Left of the first word
        ]
        # Return in the exact format your print loop expects: [box, text, confidence]
        structured_data.append([merged_box, joined_text, avg_confidence])
        
    return structured_data

def process_document_layout(ocr_results: list, y_tolerance: int = 15) -> list:
    """
    Main Director: Orchestrates the layout analysis pipeline.
    """
    # Step 1: Feature Extraction
    spatial_items = [_extract_spatial_features(item) for item in ocr_results]
    
    # Step 2: Line Clustering
    clustered_lines = _cluster_items_by_line(spatial_items, y_tolerance)
    
    # Step 3: Formatting
    final_lines = _sort_and_format_lines(clustered_lines)
    
    return final_lines

def get_raw_ocr_results(image_path: str) -> list:
    """Returns the raw OCR bounding boxes and text without formatting."""
    if not os.path.exists(image_path):
        return []
        
    ocr_engine = RapidOCR()
    results, _ = ocr_engine(image_path)
    
    return results

def test_ocr_engine(image_path: str) -> None:
    """
    Initializes the RapidOCR engine (ONNX based) and tests it on a given receipt image.
    """
    print("[SYSTEM] Initializing RapidOCR (ONNX Runtime)...")
    
    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        return
    
    # RapidOCR uses the exact same models as PaddleOCR but runs them on ONNX.
    ocr_engine = RapidOCR()
    
    print(f"[SYSTEM] Processing image: {image_path}")
    results, elapse = ocr_engine(image_path)
    
    if not results:
        print("[WARNING] No text could be extracted from the image.")
        return

    # Pass the raw results through our spatial restructuring algorithm
    structured_lines = process_document_layout(results)
    
    print(f"[SYSTEM] Extraction completed in {elapse} seconds.")
    print("-" * 50)
    
    for line in structured_lines:
        # RapidOCR returns: [bounding_box, text, confidence]
        bounding_box = line[0]        
        detected_text = line[1]           
        confidence_score = line[2]
        
        # Formatting the output for better terminal readability
        print(f"Text: {detected_text:<30} | Confidence: {confidence_score*100:.2f}%")
    
    print("-" * 50)
