"""
AttendAI — End-to-End Classroom Simulation & Performance Benchmark
======================================================================
Simulates a live classroom session with synthetic multi-face frames,
processing through the full AI pipeline:
Detection -> ArcFace Recognition -> ByteTrack -> 3D Head Pose -> Eye State (EAR) -> Device Detector -> Visual Engagement Engine -> Event Publisher
"""

import asyncio
import os
import sys
import time
import structlog

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ai_service.pipeline.orchestrator import PipelineOrchestrator

logger = structlog.get_logger(__name__)


async def run_simulation(num_frames: int = 30):
    print("\n=======================================================")
    print("🚀 AttendAI — Live Classroom AI Pipeline Benchmark")
    print("=======================================================\n")

    orchestrator = PipelineOrchestrator()
    print("1. Initializing AI Models (FaceDetector, ArcFace, ByteTrack, YOLOv8)...")
    t0 = time.time()
    await orchestrator.initialize()
    init_time = time.time() - t0
    print(f"   ✅ AI Models initialized in {init_time:.2f} seconds\n")

    session_id = "sim_session_benchmark_001"
    print(f"2. Starting AI Stream Session [{session_id}]...")
    await orchestrator.start_session_stream(session_id, source="synthetic")

    print(f"3. Processing {num_frames} classroom video frames through AI pipeline...")
    frame_times = []

    for frame_idx in range(1, num_frames + 1):
        f_t0 = time.time()
        res = await orchestrator.process_next_frame(session_id)
        f_elapsed = (time.time() - f_t0) * 1000.0  # ms
        frame_times.append(f_elapsed)

        if frame_idx % 10 == 0 or frame_idx == num_frames:
            faces_n = res.get("detected_faces_count", res.get("faces_count", 0))
            print(f"   • Frame {frame_idx:02d}/{num_frames}: {faces_n} faces | {f_elapsed:.1f} ms | Status: {res.get('status')}")

    total_time = sum(frame_times) / 1000.0
    avg_latency = sum(frame_times) / len(frame_times)
    fps = num_frames / total_time if total_time > 0 else 0

    print("\n-------------------------------------------------------")
    print("📊 BENCHMARK SUMMARY & PERFORMANCE RESULTS")
    print("-------------------------------------------------------")
    print(f" • Total Frames Processed:   {num_frames}")
    print(f" • Total Processing Time:   {total_time:.2f} seconds")
    print(f" • Average Frame Latency:   {avg_latency:.2f} ms / frame")
    print(f" • Real-Time Throughput:    {fps:.2f} FPS")
    print("-------------------------------------------------------\n")

    await orchestrator.stop_session(session_id)
    return {
        "num_frames": num_frames,
        "avg_latency_ms": round(avg_latency, 2),
        "fps": round(fps, 2),
    }


if __name__ == "__main__":
    asyncio.run(run_simulation(30))
