"""
OCR Processor using Tesseract
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
import io


class OCRProcessor:
    def __init__(self):
        # Configure tesseract if needed
        pass

    def extract_text(self, image_bytes: bytes) -> str:
        # Convert bytes to image
        image = Image.open(io.BytesIO(image_bytes))
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        # Preprocessing (optional)
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        # Extract text
        text = pytesseract.image_to_string(gray)
        return text.strip()