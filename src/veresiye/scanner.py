# src/veresiye/scanner.py
from rapidocr_onnxruntime import RapidOCR

def _extract_spatial_features(item: list) -> dict:
    """
    Task 1: Extracts only the required spatial data (Y-center, X-left) from a raw OCR item.
    """
    box = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text = item[1]
    
    # Calculate the vertical center and left starting point
    y_center = (box[0][1] + box[2][1]) / 2
    x_left = box[0][0]
    
    return {"text": text, "x_left": x_left, "y_center": y_center}

def _cluster_items_by_line(spatial_items: list, y_tolerance: int) -> list:
    """
    Task 2: Groups independent text items into logical lines based on vertical proximity.
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
    Task 3: Sorts the clustered lines top-to-bottom, and items left-to-right, then joins them.
    """
    # 1. Sort lines vertically (top to bottom)
    lines.sort(key=lambda l: l['y_center'])
    
    structured_text = []
    for line in lines:
        # 2. Sort items horizontally (left to right) within the line
        line['items'].sort(key=lambda i: i['x_left'])
        
        # 3. Join the sorted items into a single string
        joined_text = " ".join([i['text'] for i in line['items']])
        structured_text.append(joined_text)
        
    return structured_text

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

def test_ocr_engine(image_path: str) -> None:
    """
    Initializes the RapidOCR engine (ONNX based) and tests it on a given receipt image.
    """
    print("[SYSTEM] Initializing RapidOCR (ONNX Runtime)...")
    
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

if __name__ == "__main__":
    # Place one of your sample receipt images in the root directory and update the name here
    
    path = "E:/HOME/GitHub/berk/Veresiye/tests/data/migros-20250831_090053.jpg"
    
    test_ocr_engine(path)