"""OCR module using OpenCV and Tesseract."""

import cv2
import pytesseract


def capture_frame(camera_index=0):
    """Capture a single frame from the camera.

    Returns the frame as a numpy array, or None on failure.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return frame


def preprocess_image(frame):
    """Preprocess camera frame for better OCR accuracy."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold for varying lighting
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    # Denoise
    processed = cv2.medianBlur(processed, 3)
    return processed


def extract_text(frame, lang="swe+eng"):
    """Run OCR on a camera frame.

    Args:
        frame: numpy array (BGR image from OpenCV)
        lang: Tesseract language code(s). Default Swedish + English.

    Returns:
        Extracted text as string.
    """
    processed = preprocess_image(frame)
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(processed, lang=lang, config=custom_config)
    return text.strip()


def scan_and_extract(camera_index=0, lang="swe+eng"):
    """Capture from camera and extract text in one call."""
    frame = capture_frame(camera_index)
    if frame is None:
        return None, None
    text = extract_text(frame, lang=lang)
    return frame, text
