import unittest
from unittest.mock import MagicMock
from src.password_manager.service import PasswordManagerService
from src.password_manager.models import PasswordEntry
from src.storage.database import EncryptedSQLite

class TestPasswordService(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock(spec=EncryptedSQLite)
        self.mock_db.connection = MagicMock()
        self.service = PasswordManagerService(self.mock_db)

    def test_add_entry(self):
        entry = self.service.add_entry("Google", "me", "secret123", "google.com")
        
        self.assertEqual(entry.title, "Google")
        self.assertEqual(entry.password, "secret123")
        self.assertTrue(entry.created_at > 0)
        
        self.mock_db.put_encrypted_payload.assert_called_once()
        call_args = self.mock_db.put_encrypted_payload.call_args[1]
        self.assertEqual(call_args['record_id'], entry.id)
        self.assertEqual(call_args['record_type'], "password_entry")
        self.assertIsInstance(call_args['plaintext'], bytes)

    def test_get_entry(self):
        fake_entry = PasswordEntry.create("id1", "Facebook", "user", "pass")
        self.mock_db.get_decrypted_payload.return_value = fake_entry.to_bytes()
        
        result = self.service.get_entry("id1")
        self.assertEqual(result.title, "Facebook")
        self.assertEqual(result.id, "id1")
        
    def test_delete_entry(self):
        self.service.delete_entry("id1")
        self.mock_db.delete_record.assert_called_with("id1")

if __name__ == '__main__':
    unittest.main()
