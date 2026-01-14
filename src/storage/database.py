from __future__ import annotations

"""
Abstraction de stockage SQLite avec chiffrement des données.

Objectifs :
- Utiliser SQLite comme stockage local.
- Chiffrer tout le contenu sensible (payloads) avec AES-GCM.
- Ne jamais persister la clé symétrique de base en clair sur disque.

Conception :
- Le fichier SQLite n'est pas chiffré au niveau bloc, mais toutes les données
  applicatives (mots de passe, sessions, etc.) sont stockées sous forme de BLOBs
  chiffrés.
- La clé symétrique de chiffrement (clé de base) est dérivée à partir du mot de
  passe utilisateur (ou d'une clé de récupération) via PBKDF2-HMAC-SHA256.
- Un sel de dérivation spécifique à la base est stocké en clair dans une table
  meta (non sensible). La clé dérivée n'est jamais persistée telle quelle.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import os
import sqlite3
import time

from src.core.config import PASSWORDS_DIR
from src.crypto.encryption import encrypt_aes_gcm, decrypt_aes_gcm, AES_KEY_SIZE
from src.crypto.keys import generate_salt, derive_key_from_password


DEFAULT_DB_NAME = "passwords.db"
DEFAULT_DB_PATH = PASSWORDS_DIR / DEFAULT_DB_NAME

DB_SALT_KEY = "db_salt"


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _open_connection(path: Path) -> sqlite3.Connection:
    _ensure_parent_dir(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def initialize_database(path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Crée le fichier SQLite (s'il n'existe pas) et les tables de base.
    Ne dérive pas de clé : cela est géré par la couche supérieure (auth/session).
    """
    conn = _open_connection(path)
    cur = conn.cursor()

    # Table de métadonnées (inclut le sel PBKDF2 pour la clé de base)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value BLOB NOT NULL
        )
        """
    )

    # Table générique pour les enregistrements chiffrés (mots de passe, etc.)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id      TEXT PRIMARY KEY,
            type    TEXT NOT NULL,         -- e.g. 'password', 'session', ...
            payload BLOB NOT NULL          -- données chiffrées (AES-GCM)
        )
        """
    )

    conn.commit()
    return conn


def get_or_create_db_salt(conn: sqlite3.Connection) -> bytes:
    """
    Récupère (ou crée) le sel utilisé pour dériver la clé de chiffrement de la base.
    Le sel n'est pas secret et peut être stocké en clair.
    """
    cur = conn.execute("SELECT value FROM meta WHERE key = ?", (DB_SALT_KEY,))
    row = cur.fetchone()
    if row:
        return bytes(row[0])

    salt = generate_salt()
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?)",
        (DB_SALT_KEY, sqlite3.Binary(salt)),
    )
    conn.commit()
    return salt


def derive_database_key(password: str, salt: bytes) -> bytes:
    """
    Dérive une clé AES-256 à partir du mot de passe utilisateur et d'un sel.
    """
    return derive_key_from_password(password, salt, length=AES_KEY_SIZE)


@dataclass
class EncryptedRecord:
    """
    Représente un enregistrement chiffré stocké dans la table `records`.
    """

    record_id: str
    record_type: str
    payload: bytes  # BLOB chiffré (token AES-GCM)


class EncryptedSQLite:
    """
    Wrapper autour de sqlite3.Connection qui gère le chiffrement des payloads.
    """

    def __init__(self, conn: sqlite3.Connection, key: bytes):
        if len(key) != AES_KEY_SIZE:
            raise ValueError("Invalid AES key length")
        self._conn = conn
        self._key = key

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    # --- API pour les enregistrements chiffrés ---

    def put_record(self, record: EncryptedRecord) -> None:
        """
        Insère ou met à jour un enregistrement chiffré dans la table `records`.
        """
        self._conn.execute(
            "INSERT OR REPLACE INTO records (id, type, payload) VALUES (?, ?, ?)",
            (record.record_id, record.record_type, sqlite3.Binary(record.payload)),
        )
        self._conn.commit()

    def put_encrypted_payload(
        self,
        record_id: str,
        record_type: str,
        plaintext: bytes,
    ) -> None:
        """
        Chiffre un payload et le stocke dans la table `records`.
        """
        if not isinstance(plaintext, (bytes, bytearray)):
            raise ValueError("plaintext must be bytes")

        # On inclut l'identifiant comme AAD pour lier le chiffrement à l'ID
        aad = record_id.encode("utf-8")
        token = encrypt_aes_gcm(self._key, plaintext, associated_data=aad)
        rec = EncryptedRecord(record_id=record_id, record_type=record_type, payload=token)
        self.put_record(rec)

    def get_encrypted_payload(self, record_id: str) -> Optional[EncryptedRecord]:
        """
        Récupère un enregistrement chiffré depuis la table `records`.
        """
        cur = self._conn.execute(
            "SELECT id, type, payload FROM records WHERE id = ?",
            (record_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return EncryptedRecord(
            record_id=row[0],
            record_type=row[1],
            payload=bytes(row[2]),
        )

    def get_decrypted_payload(self, record_id: str, expected_type: Optional[str] = None) -> Optional[bytes]:
        """
        Récupère et déchiffre un enregistrement à partir de son identifiant.
        """
        rec = self.get_encrypted_payload(record_id)
        if rec is None:
            return None

        if expected_type is not None and rec.record_type != expected_type:
            raise ValueError(f"Unexpected record type: {rec.record_type!r}")

        aad = rec.record_id.encode("utf-8")
        return decrypt_aes_gcm(self._key, rec.payload, associated_data=aad)

    def delete_record(self, record_id: str) -> None:
        """
        Supprime un enregistrement (et donc son payload chiffré).
        """
        self._conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        self._conn.commit()

    def vacuum(self) -> None:
        """
        Compacte le fichier SQLite pour réduire la taille sur disque.
        """
        self._conn.execute("VACUUM")

