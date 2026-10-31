"""
AttendAI — FaceRecognizer Tests
"""

import numpy as np
from ai_service.pipeline.face_recognizer import (
    FaceRecognizer,
    cosine_similarity,
    l2_distance,
)


def test_cosine_similarity():
    v1 = np.ones(512, dtype=np.float32)
    v2 = np.ones(512, dtype=np.float32)
    score = cosine_similarity(v1, v2)
    assert abs(score - 1.0) < 1e-5

    v3 = -np.ones(512, dtype=np.float32)
    score_opposite = cosine_similarity(v1, v3)
    assert abs(score_opposite - (-1.0)) < 1e-5


def test_l2_distance():
    v1 = np.zeros(512, dtype=np.float32)
    v2 = np.ones(512, dtype=np.float32)
    dist = l2_distance(v1, v2)
    assert abs(dist - np.sqrt(512)) < 1e-4


def test_extract_embedding_shape_and_norm():
    recognizer = FaceRecognizer()
    dummy_face = np.random.randint(0, 255, (110, 110, 3), dtype=np.uint8)
    emb = recognizer.extract_embedding(dummy_face)

    assert emb is not None
    assert emb.shape == (512,)
    assert emb.dtype == np.float32
    # Verify unit norm
    norm = np.linalg.norm(emb)
    assert abs(norm - 1.0) < 1e-3


def test_match_face():
    recognizer = FaceRecognizer(threshold=0.6)

    # Enrolled student embeddings
    student_a_emb = np.random.rand(512).astype(np.float32)
    student_a_emb /= np.linalg.norm(student_a_emb)

    student_b_emb = np.random.rand(512).astype(np.float32)
    student_b_emb /= np.linalg.norm(student_b_emb)

    gallery = {
        "student_001": student_a_emb,
        "student_002": student_b_emb,
    }

    # Query with student_a_emb
    match_id, score = recognizer.match_face(student_a_emb, gallery)
    assert match_id == "student_001"
    assert score >= 0.99
