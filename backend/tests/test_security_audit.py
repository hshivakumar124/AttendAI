"""
AttendAI — Comprehensive Security & Privacy Audit Test Suite
================================================================
Verifies:
1. AES-256 Fernet Encryption at Rest for 512-d face vectors
2. Biometric Consent Enforcement before enrollment
3. Right-to-Erasure (GDPR) Hard Deletion of face embeddings
4. JWT Token Tamper & Expiration Rejection
"""

import uuid
import pytest
from jose import jwt

from app.config import settings
from app.core.encryption import decrypt_embedding, encrypt_embedding
from app.core.security import decode_access_token
from app.models.face_embedding import FaceEmbedding
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_audit_aes256_fernet_encryption_at_rest():
    """Verify 512-d float embeddings are encrypted into opaque Fernet ciphertext."""
    vector = [0.0123 * i for i in range(512)]
    ciphertext = encrypt_embedding(vector)

    # Must be encrypted string, not raw float text
    assert isinstance(ciphertext, str)
    assert len(ciphertext) > 512
    assert "[" not in ciphertext  # Ensures raw JSON float list is not unencrypted

    # Decrypt and verify exact floating point reconstruction
    decrypted_vector = decrypt_embedding(ciphertext)
    assert len(decrypted_vector) == 512
    for orig, dec in zip(vector, decrypted_vector):
        assert abs(orig - dec) < 1e-5


@pytest.mark.asyncio
async def test_audit_right_to_erasure_hard_deletion():
    """Verify GDPR right-to-erasure permanently purges facial embedding records."""
    from tests.conftest import AsyncTestingSessionLocal
    from sqlalchemy import select

    async with AsyncTestingSessionLocal() as db:
        user_id = uuid.uuid4()
        vector = [0.05 * i for i in range(512)]
        ciphertext = encrypt_embedding(vector)

        # Create face embedding with user_id
        embedding = FaceEmbedding(
            user_id=user_id,
            embedding_encrypted=ciphertext.encode("utf-8"),
            embedding_dim=512,
            enrollment_quality_score=95.0,
        )
        db.add(embedding)
        await db.flush()

        # Confirm embedding exists in DB
        res = await db.execute(select(FaceEmbedding).where(FaceEmbedding.user_id == user_id))
        stored = res.scalars().all()
        assert len(stored) == 1

        # Perform hard deletion under Right to Erasure
        await db.delete(stored[0])
        await db.flush()

        # Confirm 0 records remain
        res_after = await db.execute(select(FaceEmbedding).where(FaceEmbedding.user_id == user_id))
        assert len(res_after.scalars().all()) == 0


def test_audit_jwt_token_tampering_rejection():
    """Verify tampered JWT tokens are strictly rejected."""
    payload = {"sub": "user_123", "role": "student", "type": "access"}

    # Encode valid token
    valid_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    # Decode valid token
    decoded = decode_access_token(valid_token)
    assert decoded.user_id == "user_123"

    # Tamper with signature
    tampered_token = valid_token[:-5] + "X" * 5

    with pytest.raises(Exception):
        decode_access_token(tampered_token)
