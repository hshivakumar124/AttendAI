"""
AttendAI — StreamReader Tests
"""

import pytest
import numpy as np
from ai_service.ingest.stream_reader import StreamReader


def test_synthetic_stream_reader():
    reader = StreamReader(source="synthetic", target_fps=10, target_size=(640, 480))
    opened = reader.open()
    assert opened is True

    success, frame, timestamp = reader.read_frame()
    assert success is True
    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert timestamp > 0

    reader.close()
    assert reader._is_running is False


@pytest.mark.asyncio
async def test_async_frames_generator():
    reader = StreamReader(source="synthetic", target_fps=30, target_size=(320, 240))
    frames = []

    async for frame, ts, frame_num in reader.get_frames_async():
        frames.append((frame, ts, frame_num))
        if len(frames) >= 3:
            break

    reader.close()
    assert len(frames) == 3
    assert frames[0][2] == 1
    assert frames[1][2] == 2
    assert frames[2][2] == 3
