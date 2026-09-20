from pathlib import Path
from PIL import Image, UnidentifiedImageError
import pytesseract
from pytesseract import TesseractNotFoundError
from .core import settings

class OCRUnavailableError(RuntimeError):
    """Tesseract is unavailable or incorrectly configured."""

def extract_image_text(image_path: Path) -> str:
    """Extract readable notice text from a JPG/JPEG/PNG via Tesseract."""
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    try:
        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(image, config='--psm 6')
    except TesseractNotFoundError as exc:
        raise OCRUnavailableError('Image OCR is unavailable. Install Tesseract and set TESSERACT_CMD, or add Tesseract to PATH.') from exc
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('The uploaded image could not be read.') from exc
    if not text.strip():
        raise ValueError('No readable text was found in this image. Upload a clearer scan or paste the notice text.')
    return text.strip()
