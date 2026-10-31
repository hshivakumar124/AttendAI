"""
AttendAI — Biometric Data Encryption
======================================
Fernet authenticated encryption (AES-128-CBC + HMAC-SHA256) for face embedding vectors at rest.
Ensures biometric compliance and privacy protection.
Raw face vectors are encrypted before storage and decrypted only in memory during matching.
"""

import base64
import json
from typing import List, Union

import numpy as np
import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings

logger = structlog.get_logger(__name__)


def _get_fernet_key() -> bytes:
    """Derive a 256-bit Fernet key (128-bit AES encryption + 128-bit HMAC authentication) from secret_key."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"attendai_biometric_salt_v1",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))
    return key


# Singleton Fernet cipher instance
_fernet = Fernet(_get_fernet_key())


def encrypt_embedding(embedding: Union[List[float], np.ndarray]) -> str:
    """
    Encrypt a 512-dimensional float vector into a secure base64 ciphertext string.

    Args:
        embedding: List of floats or numpy array (512,)

    Returns:
        Encrypted base64 ciphertext string.
    """
    if isinstance(embedding, np.ndarray):
        float_list = embedding.astype(float).tolist()
    else:
        float_list = [float(x) for x in embedding]

    json_bytes = json.dumps(float_list).encode("utf-8")
    encrypted_bytes = _fernet.encrypt(json_bytes)
    return encrypted_bytes.decode("utf-8")


def decrypt_embedding(ciphertext: str) -> np.ndarray:
    """
    Decrypt a base64 ciphertext string back into a 512-dimensional numpy array.

    Args:
        ciphertext: Encrypted base64 string from database.

    Returns:
        np.ndarray of shape (512,) and float32 dtype.
    """
    encrypted_bytes = ciphertext.encode("utf-8")
    decrypted_json_bytes = _fernet.decrypt(encrypted_bytes)
    float_list = json.loads(decrypted_json_bytes.decode("utf-8"))
    return np.array(float_list, dtype=np.float32)
