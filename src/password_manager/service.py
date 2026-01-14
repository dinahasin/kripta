from typing import List, Optional
import uuid
from src.storage.database import EncryptedSQLite, EncryptedRecord
from src.password_manager.models import PasswordEntry

RECORD_TYPE_PASSWORD = "password_entry"

class PasswordManagerService:
    def __init__(self, db: EncryptedSQLite):
        self.db = db

    def add_entry(self, title: str, username: str, password: str, url: str = "", notes: str = "") -> PasswordEntry:
        """
        Creates and saves a new password entry.
        """
        entry_id = str(uuid.uuid4())
        entry = PasswordEntry.create(entry_id, title, username, password, url, notes)
        
        self.db.put_encrypted_payload(
            record_id=entry_id,
            record_type=RECORD_TYPE_PASSWORD,
            plaintext=entry.to_bytes()
        )
        return entry

    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        Retrieves and decrypts a password entry by ID.
        """
        plaintext = self.db.get_decrypted_payload(entry_id, expected_type=RECORD_TYPE_PASSWORD)
        if not plaintext:
            return None
        
        return PasswordEntry.from_bytes(plaintext)

    def update_entry(self, entry: PasswordEntry) -> None:
        """
        Updates an existing entry.
        """
        # Update timestamp
        import time
        entry.updated_at = int(time.time())
        
        self.db.put_encrypted_payload(
            record_id=entry.id,
            record_type=RECORD_TYPE_PASSWORD,
            plaintext=entry.to_bytes()
        )

    def delete_entry(self, entry_id: str) -> None:
        """
        Deletes an entry.
        """
        self.db.delete_record(entry_id)

    def list_entries(self) -> List[PasswordEntry]:
        """
        Lists all password entries.
        NOTE: This implementation is inefficient as it decrypts ALL entries to list them.
        In a production app, we would separate metadata (title, username) to a searchable
        (potentially blind-indexed) table. For a PoC, this is acceptable.
        """
        # Execute query directly on connection to find all IDs of type password
        cursor = self.db.connection.execute(
            "SELECT id FROM records WHERE type = ?", 
            (RECORD_TYPE_PASSWORD,)
        )
        
        entries = []
        for row in cursor:
            entry_id = row[0]
            try:
                entry = self.get_entry(entry_id)
                if entry:
                    entries.append(entry)
            except Exception as e:
                print(f"Error loading entry {entry_id}: {e}")
        
        # Sort by title
        entries.sort(key=lambda x: x.title.lower())
        return entries
