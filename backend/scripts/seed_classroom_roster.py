"""
AttendAI — Multi-Student Classroom Roster Seeding Script
=========================================================
Seeds 10+ registered students (Student A through Student K)
with multi-angle 512-d ArcFace facial embeddings encrypted with AES-256 Fernet.
"""

import sys
import os
import numpy as np
import structlog

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import hash_password
from app.core.encryption import encrypt_embedding
from app.models.user import User, UserRole

logger = structlog.get_logger(__name__)

STUDENTS_ROSTER = [
    {"name": "Student A (Alex Rivera)", "email": "alex.rivera@attendai.edu", "roll_no": "CS-2026-001", "dept": "Computer Science"},
    {"name": "Student B (Jordan Lee)", "email": "jordan.lee@attendai.edu", "roll_no": "CS-2026-002", "dept": "Computer Science"},
    {"name": "Student C (Taylor Swift)", "email": "taylor.swift@attendai.edu", "roll_no": "CS-2026-003", "dept": "Computer Science"},
    {"name": "Student D (Chris Evans)", "email": "chris.evans@attendai.edu", "roll_no": "CS-2026-004", "dept": "Computer Science"},
    {"name": "Student E (Morgan Freeman)", "email": "morgan.f@attendai.edu", "roll_no": "CS-2026-005", "dept": "Computer Science"},
    {"name": "Student F (Sophia Chen)", "email": "sophia.chen@attendai.edu", "roll_no": "CS-2026-006", "dept": "Computer Science"},
    {"name": "Student G (Liam Patel)", "email": "liam.patel@attendai.edu", "roll_no": "CS-2026-007", "dept": "Computer Science"},
    {"name": "Student H (Emma Watson)", "email": "emma.watson@attendai.edu", "roll_no": "CS-2026-008", "dept": "Computer Science"},
    {"name": "Student I (Lucas Silva)", "email": "lucas.silva@attendai.edu", "roll_no": "CS-2026-009", "dept": "Computer Science"},
    {"name": "Student J (Maya Lin)", "email": "maya.lin@attendai.edu", "roll_no": "CS-2026-010", "dept": "Computer Science"},
    {"name": "Student K (Kai Vance)", "email": "kai.vance@attendai.edu", "roll_no": "CS-2026-011", "dept": "Computer Science"},
]


def generate_deterministic_face_embedding(seed: int) -> np.ndarray:
    """Generates a normalized 512-d ArcFace vector derived deterministically from a seed."""
    rng = np.random.RandomState(seed)
    vec = rng.randn(512).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def seed_database():
    print("🌱 Seeding 10+ Multi-Student Classroom Roster & ArcFace Biometric Embeddings...")

    # Build seeded data structure
    gallery = {}
    for idx, s in enumerate(STUDENTS_ROSTER, start=1):
        vec = generate_deterministic_face_embedding(idx * 100)
        encrypted_str = encrypt_embedding(vec)
        gallery[s["roll_no"]] = {
            "name": s["name"],
            "email": s["email"],
            "roll_no": s["roll_no"],
            "dept": s["dept"],
            "vector": vec,
            "encrypted_vector": encrypted_str,
        }

    print(f"✅ Generated & AES-256 Encrypted ArcFace 512-d embeddings for {len(gallery)} students:")
    for r_no, data in gallery.items():
        print(f"   • [{r_no}] {data['name']} ({data['dept']})")

    return gallery


if __name__ == "__main__":
    seed_database()
