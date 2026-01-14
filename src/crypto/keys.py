from __future__ import annotations

"""
Primitives de gestion des clés et dérivation de clés pour Kripta.

- Génération de sel cryptographique
- Dérivation de clés à partir d'un mot de passe (PBKDF2-HMAC-SHA256)
- Hash de mot de passe (sel + PBKDF2)

Ce module NE fait aucun I/O disque et ne connaît pas SQLite ni les certificats.
"""

from dataclasses import dataclass
from typing import Tuple
import os

from hashlib import pbkdf2_hmac


PBKDF2_ITERATIONS: int = 200_000
PBKDF2_DIGEST: str = "sha256"


def generate_salt(length: int = 16) -> bytes:
    """
    Génère un sel cryptographiquement sûr.

    Args:
        length: taille du sel en octets (par défaut 16)
    """
    if length <= 0:
        raise ValueError("Salt length must be > 0")
    return os.urandom(length)


def derive_key_from_password(password: str, salt: bytes, length: int = 32) -> bytes:
    """
    Dérive une clé à partir d'un mot de passe en utilisant PBKDF2-HMAC-SHA256.

    Args:
        password: mot de passe utilisateur
        salt: sel aléatoire
        length: longueur de la clé en octets (par défaut 32 pour AES-256)
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")
    if not isinstance(salt, (bytes, bytearray)) or len(salt) == 0:
        raise ValueError("Salt must be non-empty bytes")
    if length <= 0:
        raise ValueError("Key length must be > 0")

    return pbkdf2_hmac(
        PBKDF2_DIGEST,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=length,
    )


@dataclass
class PasswordHash:
    """
    Représente un hash de mot de passe stockable (sel + dérivé PBKDF2).
    """

    salt: bytes
    derived_key: bytes


def hash_password(password: str, salt: bytes | None = None) -> PasswordHash:
    """
    Hash un mot de passe avec PBKDF2-HMAC-SHA256.

    - Génère un sel si nécessaire
    - Retourne une structure contenant sel + clé dérivée
    """
    if salt is None:
        salt = generate_salt()
    dk = derive_key_from_password(password, salt)
    return PasswordHash(salt=salt, derived_key=dk)


def verify_password(password: str, expected: PasswordHash) -> bool:
    """
    Vérifie un mot de passe contre un hash stocké.
    """
    from hmac import compare_digest

    candidate = derive_key_from_password(password, expected.salt, length=len(expected.derived_key))
    return compare_digest(candidate, expected.derived_key)

