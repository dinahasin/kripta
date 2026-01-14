from __future__ import annotations

"""
Sérialisation/désérialisation des sessions en binaire (compatible avec un schéma Protobuf).

Pour l'instant, on utilise une implémentation manuelle basée sur struct.
Le fichier src/security/protos/session.proto décrit le schéma logique.
"""

from dataclasses import dataclass
from typing import Optional
import struct
import time
import getpass


@dataclass
class SessionData:
    session_id: str
    username: str
    windows_user: str
    created_at: int
    last_seen_at: int
    expires_at: int
    is_authenticated: bool
    persistent: bool


def new_session(username: str, persistent: bool, ttl_seconds: int = 3600) -> SessionData:
    """
    Crée une nouvelle session en mémoire.
    """
    import secrets

    session_id = secrets.token_hex(16)
    now = int(time.time())
    expires = now + ttl_seconds
    windows_user = getpass.getuser()

    return SessionData(
        session_id=session_id,
        username=username,
        windows_user=windows_user,
        created_at=now,
        last_seen_at=now,
        expires_at=expires,
        is_authenticated=True,
        persistent=persistent,
    )


def touch_session(session: SessionData) -> None:
    """
    Met à jour le champ last_seen_at d'une session.
    """
    session.last_seen_at = int(time.time())


def is_session_expired(session: SessionData) -> bool:
    """
    Indique si une session est expirée.
    """
    now = int(time.time())
    return now >= session.expires_at


def serialize_session(session: SessionData) -> bytes:
    """
    Sérialise une session en binaire (format compact).

    Format :
      - len(session_id) (uint16 big-endian) + session_id utf-8
      - len(username)   (uint16) + username utf-8
      - len(windows_user) (uint16) + windows_user utf-8
      - created_at (int64)
      - last_seen_at (int64)
      - expires_at (int64)
      - is_authenticated (bool, 1 octet)
      - persistent (bool, 1 octet)
    """
    sid_bytes = session.session_id.encode("utf-8")
    user_bytes = session.username.encode("utf-8")
    win_bytes = session.windows_user.encode("utf-8")

    parts = [
        struct.pack(">H", len(sid_bytes)),
        sid_bytes,
        struct.pack(">H", len(user_bytes)),
        user_bytes,
        struct.pack(">H", len(win_bytes)),
        win_bytes,
        struct.pack(">q", session.created_at),
        struct.pack(">q", session.last_seen_at),
        struct.pack(">q", session.expires_at),
        struct.pack(">?", session.is_authenticated),
        struct.pack(">?", session.persistent),
    ]
    return b"".join(parts)


def deserialize_session(data: bytes) -> Optional[SessionData]:
    """
    Désérialise un bloc binaire en SessionData.
    Retourne None si les données sont invalides.
    """
    try:
        offset = 0

        def read_str() -> str:
            nonlocal offset
            (length,) = struct.unpack(">H", data[offset : offset + 2])
            offset += 2
            s = data[offset : offset + length].decode("utf-8")
            offset += length
            return s

        session_id = read_str()
        username = read_str()
        windows_user = read_str()

        created_at = struct.unpack(">q", data[offset : offset + 8])[0]
        offset += 8
        last_seen_at = struct.unpack(">q", data[offset : offset + 8])[0]
        offset += 8
        expires_at = struct.unpack(">q", data[offset : offset + 8])[0]
        offset += 8

        is_authenticated = struct.unpack(">?", data[offset : offset + 1])[0]
        offset += 1
        persistent = struct.unpack(">?", data[offset : offset + 1])[0]
        offset += 1

        return SessionData(
            session_id=session_id,
            username=username,
            windows_user=windows_user,
            created_at=created_at,
            last_seen_at=last_seen_at,
            expires_at=expires_at,
            is_authenticated=is_authenticated,
            persistent=persistent,
        )
    except Exception:
        return None

