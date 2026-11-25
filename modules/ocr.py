
import os
import shutil

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# Common Windows Tesseract installation path
WINDOWS_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def configure_tesseract():
    """Find and configure the Tesseract OCR executable."""

    if shutil.which("tesseract"):
        return

    if os.path.exists(WINDOWS_TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = (
            WINDOWS_TESSERACT_PATH
        )
        return

    raise RuntimeError(
        "Tesseract OCR is not installed or not configured. "
        "Install Tesseract OCR and try again."
    )


def preprocess_image(image):
    """Improve image quality before extracting text."""

    image = image.convert("RGB")

    # Make text easier to read
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    # Enlarge small images for better OCR
    width, height = image.size

    if width < 1200:
        scale = 1200 / width
        image = image.resize(
            (int(width * scale), int(height * scale))
        )

    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = ImageEnhance.Sharpness(image).enhance(2.0)
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image


def extract_text(image):
    """
    Extract ingredient text from a PIL image.

    Args:
        image: PIL Image object

    Returns:
        Extracted text as a string
    """

    configure_tesseract()

    processed_image = preprocess_image(image)

    # PSM 6 assumes a block of text, suitable for labels
    config = "--oem 3 --psm 6"

    text = pytesseract.image_to_string(
        processed_image,
        config=config,
        lang="eng",
    )

    return text.strip()
