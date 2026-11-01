import os
import cv2
import numpy as np
from collections import Counter
from rapidocr_onnxruntime import RapidOCR

class VisionEngine:
    def __init__(self):
        self.name = "Vision & OCR Engine"
        # Initializes the ONNX OCR model (runs entirely locally on CPU)
        self.ocr = RapidOCR()

    def get_dominant_colors(self, image_path: str, k: int = 3) -> list:
        """Extracts dominant hex colors from an image using K-Means clustering."""
        if not os.path.exists(image_path):
            return []
        
        # Read and resize heavily to make processing instant
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (100, 100), interpolation=cv2.INTER_AREA)
        
        # Reshape array for K-Means math
        pixels = img.reshape((-1, 3))
        pixels = np.float32(pixels)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert RGB centers to Hex codes
        centers = np.uint8(centers)
        hex_colors = ["#{:02x}{:02x}{:02x}".format(c[0], c[1], c[2]) for c in centers]
        return hex_colors

    def get_in_image_text(self, image_path: str) -> str:
        """Runs ONNX RapidOCR to find text inside screenshots or photographs."""
        if not os.path.exists(image_path):
            return ""
        
        result, _ = self.ocr(image_path)
        if result:
            # result structure: [ [box, text, confidence], ... ]
            # Filter out low-confidence hallucinated text
            texts = [line[1] for line in result if line[2] > 0.70]
            return " | ".join(texts)
        return ""

    def analyze(self, raw_data: dict) -> dict:
        """Processes all cached thumbnails to build a visual fingerprint."""
        if not raw_data or not raw_data.get("posts"):
            return {"error": "No posts to analyze."}

        all_hex_colors = []
        extracted_snippets = []

        print(f"[*] Vision Engine scanning {len(raw_data['posts'])} images...")

        for post in raw_data["posts"]:
            img_path = post.get("local_thumbnail_path")
            
            if img_path and os.path.exists(img_path):
                # 1. Aesthetic Palette Extraction
                colors = self.get_dominant_colors(img_path)
                all_hex_colors.extend(colors)
                
                # 2. Hidden Text OCR
                text = self.get_in_image_text(img_path)
                # Ignore tiny fragments or noise
                if text and len(text) > 5: 
                    extracted_snippets.append(text)

        # Count the most frequent dominant colors across all posts
        dominant_palette = [color for color, count in Counter(all_hex_colors).most_common(5)]

        return {
            "aesthetic_palette": dominant_palette,
            "in_image_text_snippets": extracted_snippets,
            "total_ocr_hits": len(extracted_snippets)
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    import json
    
    if os.path.exists("raw_profile.json"):
        with open("raw_profile.json", "r", encoding="utf-8") as f:
            sample_data = json.load(f)
            
        engine = VisionEngine()
        result = engine.analyze(sample_data)
        
        print("\n[*] Vision Engine Analysis Complete:")
        print(json.dumps(result, indent=2))
    else:
        print("[!] raw_profile.json not found. Run fetcher.py first.")
