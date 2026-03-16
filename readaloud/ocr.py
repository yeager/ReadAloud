"""OCR module using OpenCV and Tesseract."""

import cv2
import numpy as np
import pytesseract

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp


def capture_frame(camera_index=0):
    """Capture a single frame from the camera.

    Returns the frame as a numpy array, or None on failure.
    """
    # Try GStreamer first for better camera support on Linux
    try:
        return capture_frame_gstreamer(camera_index)
    except Exception:
        pass
    
    # Fallback to OpenCV
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return frame


def capture_frame_gstreamer(camera_index=0):
    """Capture frame using GStreamer pipeline.
    
    This provides better camera support and integration with PipeWire.
    """
    Gst.init(None)
    
    # Build pipeline for camera capture
    pipeline_desc = f"""
        v4l2src device=/dev/video{camera_index} ! 
        videoconvert ! 
        video/x-raw,format=RGB ! 
        appsink name=sink emit-signals=true sync=false max-buffers=1 drop=true
    """
    
    pipeline = Gst.parse_launch(pipeline_desc)
    appsink = pipeline.get_by_name("sink")
    
    pipeline.set_state(Gst.State.PLAYING)
    
    # Wait for a frame
    import time
    timeout = 5.0  # 5 second timeout
    start_time = time.time()
    
    frame = None
    while time.time() - start_time < timeout:
        sample = appsink.try_pull_sample(Gst.SECOND)
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            
            # Extract frame info
            struct = caps.get_structure(0)
            width = struct.get_int("width")[1]
            height = struct.get_int("height")[1]
            
            # Get buffer data
            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                # Convert to numpy array (RGB format)
                frame_data = np.frombuffer(map_info.data, dtype=np.uint8)
                frame = frame_data.reshape((height, width, 3))
                # Convert RGB to BGR for OpenCV compatibility
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                buf.unmap(map_info)
                break
        
        time.sleep(0.1)
    
    pipeline.set_state(Gst.State.NULL)
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
