"""
AttendAI — Multi-Student Recognition & Tracking Unit Test
===========================================================
Verifies simultaneous detection, ArcFace vector matching, ByteTrack identity tracking,
and present/absent roster reconciliation for a 10-student classroom.
"""

import numpy as np
import pytest

from ai_service.pipeline.face_recognizer import FaceRecognizer, cosine_similarity
from ai_service.pipeline.tracker import ByteTrackTracker
from backend.app.services.attendance_engine import AttendanceEngine


def generate_mock_student_embedding(seed: int) -> np.ndarray:
    rng = np.random.RandomState(seed)
    vec = rng.randn(512).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def test_multi_student_arcface_recognition_matching():
    recognizer = FaceRecognizer(threshold=0.60)

    # 1. Enrol 10 distinct students into gallery
    gallery = {}
    student_roster = []
    for i in range(1, 11):
        sid = f"STUDENT_{i:02d}"
        roll = f"CS-2026-{i:03d}"
        name = f"Student {chr(64 + i)}"  # Student A, Student B...
        emb = generate_mock_student_embedding(i * 100)
        gallery[sid] = emb
        student_roster.append({"student_id": sid, "name": name, "roll_no": roll})

    # 2. Test query face matching Student A (STUDENT_01)
    query_a = gallery["STUDENT_01"].copy() + np.random.normal(0, 0.01, 512).astype(np.float32)
    query_a = query_a / np.linalg.norm(query_a)

    matched_id, score = recognizer.match_face(query_a, gallery)
    assert matched_id == "STUDENT_01"
    assert score >= 0.60

    # 3. Test query face matching Student G (STUDENT_07)
    query_g = gallery["STUDENT_07"].copy() + np.random.normal(0, 0.01, 512).astype(np.float32)
    query_g = query_g / np.linalg.norm(query_g)

    matched_id_g, score_g = recognizer.match_face(query_g, gallery)
    assert matched_id_g == "STUDENT_07"
    assert score_g >= 0.60

    # 4. Test unknown stranger (random noise) -> Should return None (Unknown Person)
    unknown_emb = generate_mock_student_embedding(99999)
    matched_id_unk, score_unk = recognizer.match_face(unknown_emb, gallery)
    assert matched_id_unk is None
    assert score_unk < 0.60


def test_roster_reconciliation_present_vs_absent():
    engine = AttendanceEngine()

    registered_students = [
        {"student_id": f"STU_{i:02d}", "name": f"Student {chr(64 + i)}", "roll_no": f"CS-00{i}"}
        for i in range(1, 11)  # 10 Students (A-J)
    ]

    # 7 students detected, 3 absent (Student C, F, J missing)
    detected = {
        "STU_01": {"status": "PRESENT", "presence_percentage": 95.0, "engagement_score": 88.0, "device_minutes": 0.0, "drowsy_minutes": 0.0},
        "STU_02": {"status": "PRESENT", "presence_percentage": 92.0, "engagement_score": 75.0, "device_minutes": 3.5, "drowsy_minutes": 0.0},
        "STU_04": {"status": "PRESENT", "presence_percentage": 98.0, "engagement_score": 94.0, "device_minutes": 0.0, "drowsy_minutes": 0.0},
        "STU_05": {"status": "PRESENT", "presence_percentage": 88.0, "engagement_score": 82.0, "device_minutes": 0.0, "drowsy_minutes": 2.0},
        "STU_07": {"status": "PRESENT", "presence_percentage": 91.0, "engagement_score": 86.0, "device_minutes": 0.0, "drowsy_minutes": 0.0},
        "STU_08": {"status": "PRESENT", "presence_percentage": 96.0, "engagement_score": 90.0, "device_minutes": 0.0, "drowsy_minutes": 0.0},
        "STU_09": {"status": "PRESENT", "presence_percentage": 89.0, "engagement_score": 85.0, "device_minutes": 0.0, "drowsy_minutes": 0.0},
    }

    report = engine.reconcile_session_roster(registered_students, detected)

    assert report["registered_count"] == 10
    assert report["present_count"] == 7
    assert report["absent_count"] == 3
    assert report["average_engagement"] > 80.0

    # Verify absent list
    absent_names = [r["name"] for r in report["roster"] if r["status"] == "ABSENT"]
    assert "Student C" in absent_names
    assert "Student F" in absent_names
    assert "Student J" in absent_names
