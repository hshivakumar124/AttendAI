"""
AttendAI — Biometric AES-256 Encryption Tests
"""

import numpy as np
from app.core.encryption import encrypt_embedding, decrypt_embedding


def test_encrypt_and_decrypt_embedding():
    # 512-dimensional vector
    original_vector = np.random.randn(512).astype(np.float32)

    # Encrypt
    encrypted_str = encrypt_embedding(original_vector)
    assert isinstance(encrypted_str, str)
    assert len(encrypted_str) > 100
    assert encrypted_str != str(original_vector.tolist())

    # Decrypt
    decrypted_vector = decrypt_embedding(encrypted_str)
    assert isinstance(decrypted_vector, np.ndarray)
    assert decrypted_vector.shape == (512,)
    assert np.allclose(original_vector, decrypted_vector, atol=1e-5)


def test_encryption_output_is_unique():
    """Fernet generates unique ciphertexts with different IVs for identical plaintext."""
    vector = [0.12345] * 512
    enc1 = encrypt_embedding(vector)
    enc2 = encrypt_embedding(vector)
    assert enc1 != enc2  # Different IVs

    # Both decrypt to exact same values
    dec1 = decrypt_embedding(enc1)
    dec2 = decrypt_embedding(enc2)
    assert np.allclose(dec1, dec2, atol=1e-5)
