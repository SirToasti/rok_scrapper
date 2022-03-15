try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import os
print(os.environ['PATH'])
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

# Simple image to string
print(pytesseract.image_to_string(Image.open('assets/sample.jpg')))