"""
AttendAI — Simulation Benchmark Automated Test
"""

import pytest
from ai_service.pipeline.orchestrator import PipelineOrchestrator


@pytest.mark.asyncio
async def test_end_to_end_classroom_simulation_benchmark():
    orchestrator = PipelineOrchestrator()
    await orchestrator.initialize()

    session_id = "test_sim_session_999"
    await orchestrator.start_session_stream(session_id, source="synthetic")

    last_res = None
    for _ in range(10):
        res = await orchestrator.process_next_frame(session_id)
        assert res["status"] == "ok"
        assert "detected_faces_count" in res or "faces_count" in res
        assert "tracks" in res
        last_res = res

    assert last_res is not None
    assert last_res["frame_number"] >= 10

    await orchestrator.stop_session(session_id)
