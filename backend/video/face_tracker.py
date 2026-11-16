import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional
from backend.core.logger import logger

class FaceTracker:
    def __init__(self):
        # Initialize OpenCV Haar Cascade Face Detector as fast, zero-dependency baseline
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def calculate_speaker_center(self, video_path: Path, start_time: float, duration: float, sample_interval: float = 1.0) -> float:
        """
        Samples frames every `sample_interval` seconds during the clip segment,
        detects face bounding boxes, and returns the smoothed horizontal center ratio (0.0 to 1.0).
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning(f"Could not open video {video_path} for face tracking")
            return 0.5

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920.0
        
        centers = []
        t = start_time
        end_time = start_time + duration

        while t < end_time:
            frame_no = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # Resize frame to low resolution for fast processing
            h, w = frame.shape[:2]
            small = cv2.resize(frame, (320, int(320 * h / w)))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=4, minSize=(30, 30))
            if len(faces) > 0:
                # Pick largest face (primary speaker)
                largest = max(faces, key=lambda b: b[2] * b[3])
                fx, fy, fw, fh = largest
                center_norm = (fx + fw / 2.0) / 320.0
                centers.append(center_norm)

            t += sample_interval

        cap.release()

        if not centers:
            return 0.5 # Default middle

        # Median filter to eliminate outliers and smooth camera tracking
        median_center = float(np.median(centers))
        # Clamp to avoid panning too far out of frame bounds for 9:16 crop
        clamped = max(0.2, min(0.8, median_center))
        logger.info(f"Face tracking computed horizontal center: {round(clamped, 2)} for {video_path.name}")
        return round(clamped, 2)

face_tracker = FaceTracker()
