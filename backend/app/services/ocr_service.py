import pytesseract
from PIL import Image
import io

# Point pytesseract to the Tesseract executable on Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Takes raw image bytes, runs OCR, and returns the extracted text.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"__OCR_ERROR__: {str(e)}"