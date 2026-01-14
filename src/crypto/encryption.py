from __future__ import annotations

"""
Primitives de chiffrement symétrique pour Kripta.

- AES-256-GCM pour chiffrement authentifié (confidentialité + intégrité)
- Format de token versionné, auto-contenu, adapté au stockage en BLOB SQLite
"""

from typing import Optional
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


AES_KEY_SIZE = 32  # AES-256
AES_NONCE_SIZE = 12  # Recommandé pour GCM


def generate_aes_key() -> bytes:
    """Génère une clé AES-256 aléatoire."""
    return os.urandom(AES_KEY_SIZE)


def encrypt_aes_gcm(
    key: bytes,
    plaintext: bytes,
    associated_data: Optional[bytes] = None,
) -> bytes:
    """
    Chiffre un message avec AES-256-GCM.

    Format du token retourné :
        b"V1" || nonce (12 octets) || ciphertext+tag
    """
    if not isinstance(key, (bytes, bytearray)) or len(key) != AES_KEY_SIZE:
        raise ValueError("AES-GCM key must be 32 bytes (AES-256)")
    if not isinstance(plaintext, (bytes, bytearray)):
        raise ValueError("Plaintext must be bytes")

    aesgcm = AESGCM(key)
    nonce = os.urandom(AES_NONCE_SIZE)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    return b"V1" + nonce + ct


def decrypt_aes_gcm(
    key: bytes,
    token: bytes,
    associated_data: Optional[bytes] = None,
) -> bytes:
    """
    Déchiffre un token AES-256-GCM au format encrypt_aes_gcm().
    """
    if not isinstance(key, (bytes, bytearray)) or len(key) != AES_KEY_SIZE:
        raise ValueError("AES-GCM key must be 32 bytes (AES-256)")
    if not isinstance(token, (bytes, bytearray)) or len(token) < 2 + AES_NONCE_SIZE + 16:
        raise ValueError("Invalid token length")

    if not token.startswith(b"V1"):
        raise ValueError("Unsupported encryption token version")

    nonce = token[2 : 2 + AES_NONCE_SIZE]
    ct = token[2 + AES_NONCE_SIZE :]

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, associated_data)

