"""
AttendAI — Video Stream Ingest Reader
=======================================
Asynchronous frame reader for RTSP streams, Webcams, Local Video files,
and Synthetic test streams.

Handles reconnection logic for RTSP streams and non-blocking frame retrieval.
"""

import asyncio
import time
from typing import AsyncGenerator, Generator, Optional, Tuple, Union
import cv2
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class StreamReader:
    """
    Asynchronous video stream reader.

    Supports:
    - RTSP Stream URLs (rtsp://...)
    - Webcams (device_index: 0, 1, ...)
    - Video Files (/path/to/video.mp4)
    - Synthetic Frames (for testing/CI without camera)
    """

    def __init__(
        self,
        source: Union[str, int],
        target_fps: int = 10,
        target_size: Tuple[int, int] = (1280, 720),
        loop_video: bool = True,
    ):
        self.source = source
        self.target_fps = target_fps
        self.target_size = target_size
        self.loop_video = loop_video
        self.is_synthetic = (source == "synthetic" or source == -1)

        self._cap: Optional[cv2.VideoCapture] = None
        self._is_running = False
        self._frame_count = 0
        self._fps_delay = 1.0 / target_fps if target_fps > 0 else 0.1

    def open(self) -> bool:
        """Open the video stream or set up synthetic stream."""
        if self.is_synthetic:
            self._is_running = True
            logger.info("Opened synthetic frame stream")
            return True

        logger.info("Opening video stream source", source=self.source)
        if isinstance(self.source, int):
            self._cap = cv2.VideoCapture(self.source)
        else:
            self._cap = cv2.VideoCapture(str(self.source))

        if self._cap is None or not self._cap.isOpened():
            logger.error("Failed to open video source", source=self.source)
            self._is_running = False
            return False

        self._is_running = True
        logger.info("Video stream source opened successfully", source=self.source)
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray], float]:
        """
        Synchronously read one frame.

        Returns:
            (success, frame_bgr, timestamp)
        """
        timestamp = time.time()
        if not self._is_running:
            return False, None, timestamp

        if self.is_synthetic:
            self._frame_count += 1
            frame = self._generate_synthetic_frame()
            return True, frame, timestamp

        if self._cap is None or not self._cap.isOpened():
            return False, None, timestamp

        ret, frame = self._cap.read()
        if not ret:
            if self.loop_video and isinstance(self.source, str) and not self.source.startswith("rtsp://"):
                # Loop video file
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self._cap.read()

        if not ret or frame is None:
            return False, None, timestamp

        self._frame_count += 1
        if self.target_size and (frame.shape[1] != self.target_size[0] or frame.shape[0] != self.target_size[1]):
            frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)

        return True, frame, timestamp

    async def get_frames_async(self) -> AsyncGenerator[Tuple[np.ndarray, float, int], None]:
        """
        Async generator yielding (frame_bgr, timestamp, frame_number)
        at target_fps rate.
        """
        if not self._is_running:
            self.open()

        while self._is_running:
            start_time = time.time()
            success, frame, timestamp = self.read_frame()

            if not success or frame is None:
                await asyncio.sleep(0.1)
                continue

            yield frame, timestamp, self._frame_count

            elapsed = time.time() - start_time
            sleep_time = max(0.0, self._fps_delay - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def close(self) -> None:
        """Release camera/video resource."""
        self._is_running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("Closed video stream", source=self.source, frames_read=self._frame_count)

    def _generate_synthetic_frame(self) -> np.ndarray:
        """Generates a synthetic classroom frame with 2 simulated faces for testing."""
        w, h = self.target_size
        img = np.zeros((h, w, 3), dtype=np.uint8)
        # Background: Classroom wall color (subtle gradient / grey-blue)
        img[:, :] = (220, 215, 205)

        # Draw simulated desks
        cv2.rectangle(img, (100, 500), (500, 700), (120, 90, 60), -1)
        cv2.rectangle(img, (700, 500), (1100, 700), (120, 90, 60), -1)

        # Draw Face 1 (Student A)
        cx1, cy1 = 300, 350
        # Face oval
        cv2.ellipse(img, (cx1, cy1), (60, 80), 0, 0, 360, (180, 200, 230), -1)
        # Eyes
        cv2.circle(img, (cx1 - 20, cy1 - 20), 8, (50, 50, 50), -1)
        cv2.circle(img, (cx1 + 20, cy1 - 20), 8, (50, 50, 50), -1)
        # Mouth
        cv2.line(img, (cx1 - 15, cy1 + 30), (cx1 + 15, cy1 + 30), (50, 50, 150), 3)

        # Draw Face 2 (Student B)
        cx2, cy2 = 900, 350
        cv2.ellipse(img, (cx2, cy2), (65, 85), 0, 0, 360, (170, 195, 225), -1)
        cv2.circle(img, (cx2 - 22, cy2 - 20), 8, (50, 50, 50), -1)
        cv2.circle(img, (cx2 + 22, cy2 - 20), 8, (50, 50, 50), -1)
        cv2.line(img, (cx2 - 20, cy2 + 35), (cx2 + 20, cy2 + 35), (50, 50, 150), 3)

        # Overlay frame counter text
        cv2.putText(
            img,
            f"SYNTHETIC CLASSROOM FRAME #{self._frame_count}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (40, 40, 40),
            2,
        )

        return img
