"""
AttendAI — AI Inference Service Entry Point
=============================================
Standalone FastAPI service for all AI processing.
Runs independently from the main backend.
GPU-accelerated inference with CPU fallback.
"""

import base64
import cv2
import numpy as np
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from config.ai_config import ai_settings
from pipeline.orchestrator import PipelineOrchestrator

logger = structlog.get_logger(__name__)

# Global pipeline orchestrator (initialized once at startup)
orchestrator: PipelineOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator

    logger.info("🤖 AttendAI AI Service starting", cuda=ai_settings.cuda_device)

    # Initialize the AI pipeline (loads models into GPU/CPU memory)
    orchestrator = PipelineOrchestrator()
    await orchestrator.initialize()
    app.state.orchestrator = orchestrator

    logger.info("✅ AI Pipeline ready", device=orchestrator.device)
    yield

    # Shutdown
    logger.info("🔴 AI Service shutting down")
    if orchestrator:
        await orchestrator.shutdown()


app = FastAPI(
    title="AttendAI — AI Inference Service",
    description="GPU-accelerated AI pipeline: face detection, recognition, tracking, engagement estimation",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "AI Inference",
        "device": orchestrator.device if orchestrator else "not_initialized",
        "models_loaded": orchestrator.models_loaded if orchestrator else False,
    }


@app.get("/device-info")
async def device_info():
    """Returns GPU/CPU info for the inference device."""
    if not orchestrator:
        return {"device": "not_initialized"}
    return orchestrator.get_device_info()


@app.post("/infer-frame-base64")
async def infer_frame_base64(payload: dict = Body(...)):
    """
    Receives live base64 JPEG image payload from browser webcam canvas.
    Runs Face Detection, ArcFace Vector Recognition, ByteTrack, 3D Head Pose, EAR Drowsiness, and Device Detection.
    """
    if not orchestrator:
        return {"status": "error", "message": "AI Orchestrator not initialized"}

    image_data = payload.get("image_base64", "")
    if "," in image_data:
        image_data = image_data.split(",")[1]

    try:
        raw_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"status": "error", "message": "Failed to decode frame"}

        # The gallery is supplied by the authenticated backend.  It is never
        # persisted by this service; it exists only for this inference call.
        raw_gallery = payload.get("enrolled_gallery") or {}
        enrolled_gallery = {
            student_id: np.asarray(embedding, dtype=np.float32)
            for student_id, embedding in raw_gallery.items()
            if isinstance(embedding, list)
        }
        return orchestrator.process_direct_frame(frame, enrolled_gallery=enrolled_gallery)
    except Exception as e:
        logger.error("Failed to process base64 live frame", error=str(e))
        return {"status": "error", "message": str(e)}


@app.post("/sessions/{session_id}/start-ai")
async def start_session_ai(session_id: str, source: str = "synthetic"):
    """Starts AI processing stream for a session."""
    if not orchestrator:
        return {"status": "error", "message": "AI Orchestrator not initialized"}
    await orchestrator.start_session_stream(session_id, source=source)
    return {"status": "started", "session_id": session_id, "source": source}


@app.post("/sessions/{session_id}/process-frame")
async def process_frame(session_id: str):
    """Processes the next single frame in an active session."""
    if not orchestrator:
        return {"status": "error", "message": "AI Orchestrator not initialized"}
    return await orchestrator.process_next_frame(session_id)


@app.post("/sessions/{session_id}/stop-ai")
async def stop_session_ai(session_id: str):
    """Stops AI processing for a session."""
    if not orchestrator:
        return {"status": "error", "message": "AI Orchestrator not initialized"}
    await orchestrator.stop_session(session_id)
    return {"status": "stopped", "session_id": session_id}
