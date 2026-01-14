from __future__ import annotations

"""
Gestion des sessions d'authentification applicatives.

Responsabilités :
- Créer / valider / expirer des sessions liées à l'utilisateur Windows.
- Sérialiser les sessions via session_protobuf.
- Chiffrer les sessions avant stockage (via storage.database.EncryptedSQLite).

Ce module NE gère PAS l'UI : il expose uniquement des primitives métier.
"""

from dataclasses import dataclass
from typing import Optional
import time
import getpass

from src.storage.database import (
    initialize_database,
    get_or_create_db_salt,
    derive_database_key,
    EncryptedSQLite,
)
from src.security.session_protobuf import (
    SessionData,
    new_session,
    touch_session,
    is_session_expired,
    serialize_session,
    deserialize_session,
)


SESSION_RECORD_TYPE = "session"
CURRENT_SESSION_ID = "current_session"


@dataclass
class SessionConfig:
    """
    Paramètres de configuration de session.
    """

    persistent_ttl: int = 7 * 24 * 3600  # 7 jours
    temporary_ttl: int = 3600  # 1 heure


def _open_encrypted_store(master_password: str) -> EncryptedSQLite:
    """
    Ouvre la base SQLite chiffrée pour les sessions et dérive la clé.
    """
    conn = initialize_database()
    salt = get_or_create_db_salt(conn)
    key = derive_database_key(master_password, salt)
    return EncryptedSQLite(conn, key)


def create_or_restore_session(
    master_password: str,
    username: str,
    persistent: bool,
    config: Optional[SessionConfig] = None,
) -> SessionData:
    """
    Crée une nouvelle session ou restaure une session persistante si elle existe et est valide.

    - Dérive la clé de base depuis le mot de passe maître.
    - Tente de lire une session existante dans la base.
    - Si la session est valide (non expirée, user Windows identique) => retour.
    - Sinon, crée une nouvelle session et l'enregistre.
    """
    if config is None:
        config = SessionConfig()

    store = _open_encrypted_store(master_password)

    # Tenter de restaurer une session existante
    rec = store.get_encrypted_payload(CURRENT_SESSION_ID, expected_type=SESSION_RECORD_TYPE)
    if rec is not None:
        data = rec
    else:
        data = None

    if data is not None:
        session_bytes = store.get_decrypted_payload(CURRENT_SESSION_ID, expected_type=SESSION_RECORD_TYPE)
        if session_bytes:
            session = deserialize_session(session_bytes)
            if (
                session
                and not is_session_expired(session)
                and session.windows_user == getpass.getuser()
            ):
                # Session valide, on la met à jour (last_seen) et on la retourne
                touch_session(session)
                store.put_encrypted_payload(
                    CURRENT_SESSION_ID,
                    SESSION_RECORD_TYPE,
                    serialize_session(session),
                )
                return session

    # Sinon, créer une nouvelle session
    ttl = config.persistent_ttl if persistent else config.temporary_ttl
    session = new_session(username=username, persistent=persistent, ttl_seconds=ttl)
    store.put_encrypted_payload(
        CURRENT_SESSION_ID,
        SESSION_RECORD_TYPE,
        serialize_session(session),
    )
    return session


def invalidate_session(master_password: str) -> None:
    """
    Invalide la session en cours (supprime l'enregistrement).
    """
    store = _open_encrypted_store(master_password)
    store.delete_record(CURRENT_SESSION_ID)

