import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from backend.core.logger import logger

class FaceTracker:
    def __init__(self):
        # Fast OpenCV Haar Cascade Face Detector as baseline
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def analyze_speakers(
        self,
        video_path: Path,
        start_time: float,
        duration: float,
        sample_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Samples frames across the clip and determines:
        1. Single speaker horizontal center (0.0 - 1.0)
        2. Whether two distinct speakers coexist (Podcast / Interview 2-shot split candidate)
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning(f"Could not open video {video_path} for face tracking")
            return {
                "layout": "single",
                "single_center_x": 0.5,
                "left_center_x": 0.3,
                "right_center_x": 0.7,
            }

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        centers = []
        dual_face_samples = []

        t = start_time
        end_time = start_time + duration
        total_samples = 0

        consecutive_read_failures = 0
        while t < end_time:
            frame_no = int(t * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret or frame is None:
                consecutive_read_failures += 1
                if consecutive_read_failures >= 5:
                    break
                t += sample_interval
                continue

            consecutive_read_failures = 0
            total_samples += 1
            h, w = frame.shape[:2]
            small_w = 320
            small_h = int(320 * h / w)
            small = cv2.resize(frame, (small_w, small_h))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=4, minSize=(25, 25)
            )

            if len(faces) > 0:
                # 1. Primary face center
                largest = max(faces, key=lambda b: b[2] * b[3])
                fx, fy, fw, fh = largest
                centers.append((fx + fw / 2.0) / float(small_w))

                # 2. Check for two distinct coexisting faces
                if len(faces) >= 2:
                    # Sort faces by area, take top 2
                    sorted_by_size = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)[:2]
                    # Sort left-to-right
                    sorted_x = sorted(sorted_by_size, key=lambda b: b[0])
                    f1, f2 = sorted_x[0], sorted_x[1]
                    c1 = (f1[0] + f1[2] / 2.0) / float(small_w)
                    c2 = (f2[0] + f2[2] / 2.0) / float(small_w)

                    # Separation between two faces must be at least 20% of frame width
                    if (c2 - c1) >= 0.20:
                        dual_face_samples.append((c1, c2))

            t += sample_interval

        cap.release()

        # Compute single speaker median center
        if centers:
            median_single = float(np.median(centers))
            clamped_single = max(0.2, min(0.8, median_single))
        else:
            clamped_single = 0.5

        # Check if qualifying for Dual-Speaker Split Layout
        is_split = False
        left_c = 0.3
        right_c = 0.7

        if total_samples > 0 and len(dual_face_samples) / float(total_samples) >= 0.35:
            is_split = True
            left_c = float(np.median([s[0] for s in dual_face_samples]))
            right_c = float(np.median([s[1] for s in dual_face_samples]))
            left_c = max(0.15, min(0.45, left_c))
            right_c = max(0.55, min(0.85, right_c))
            logger.info(f"Podcast Split layout detected: left={round(left_c, 2)}, right={round(right_c, 2)}")

        return {
            "layout": "split" if is_split else "single",
            "single_center_x": round(clamped_single, 2),
            "left_center_x": round(left_c, 2),
            "right_center_x": round(right_c, 2),
        }

    def calculate_speaker_center(self, video_path: Path, start_time: float, duration: float, sample_interval: float = 1.0) -> float:
        """Backward compatible helper returning single speaker center."""
        res = self.analyze_speakers(video_path, start_time, duration, sample_interval)
        return res["single_center_x"]

face_tracker = FaceTracker()
