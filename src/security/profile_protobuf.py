"""
Sérialisation/désérialisation Protobuf pour le profil de sécurité.
Pour l'instant, on utilise une approche simplifiée sans générer le code Protobuf.
"""

from pathlib import Path
from typing import Optional
from src.security.bootstrap import SecurityProfileData


def _save_security_profile(profile: SecurityProfileData) -> None:
    """
    Sauvegarde le profil de sécurité en format binaire simple (à remplacer par Protobuf réel).
    """
    from src.core.config import SECURITY_PROFILE_FILE
    import struct
    
    # Format simple : len(salt) + salt + len(hash) + hash + has_recovery (bool) + 
    # len(encrypted_recovery) + encrypted_recovery + created_at + updated_at + len(username) + username
    
    data = (
        struct.pack(">I", len(profile.master_password_salt)) + profile.master_password_salt +
        struct.pack(">I", len(profile.master_password_hash)) + profile.master_password_hash +
        struct.pack(">?", profile.has_recovery_key) +
        struct.pack(">I", len(profile.encrypted_recovery_key) if profile.encrypted_recovery_key else 0) +
        (profile.encrypted_recovery_key or b"") +
        struct.pack(">Q", profile.created_at) +
        struct.pack(">Q", profile.updated_at) +
        struct.pack(">I", len(profile.username.encode('utf-8'))) +
        profile.username.encode('utf-8')
    )
    
    with open(SECURITY_PROFILE_FILE, "wb") as f:
        f.write(data)


def _load_security_profile() -> Optional[SecurityProfileData]:
    """
    Charge le profil de sécurité depuis le fichier.
    """
    from src.core.config import SECURITY_PROFILE_FILE
    import struct
    
    if not SECURITY_PROFILE_FILE.exists():
        return None
    
    try:
        with open(SECURITY_PROFILE_FILE, "rb") as f:
            data = f.read()
        
        offset = 0
        
        # Lire salt
        salt_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        salt = data[offset:offset+salt_len]
        offset += salt_len
        
        # Lire hash
        hash_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        pwd_hash = data[offset:offset+hash_len]
        offset += hash_len
        
        # Lire has_recovery_key
        has_recovery = struct.unpack(">?", data[offset:offset+1])[0]
        offset += 1
        
        # Lire encrypted_recovery_key
        recovery_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        encrypted_recovery = data[offset:offset+recovery_len] if recovery_len > 0 else None
        offset += recovery_len
        
        # Lire created_at
        created_at = struct.unpack(">Q", data[offset:offset+8])[0]
        offset += 8
        
        # Lire updated_at
        updated_at = struct.unpack(">Q", data[offset:offset+8])[0]
        offset += 8
        
        # Lire username
        username_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        username = data[offset:offset+username_len].decode('utf-8')
        
        return SecurityProfileData(
            master_password_salt=salt,
            master_password_hash=pwd_hash,
            has_recovery_key=has_recovery,
            encrypted_recovery_key=encrypted_recovery,
            created_at=created_at,
            updated_at=updated_at,
            username=username,
        )
    except Exception:
        return None


def is_security_profile_initialized() -> bool:
    """
    Vérifie si le profil de sécurité existe et est valide.
    """
    from src.security.bootstrap import verify_user_certificate
    
    profile = _load_security_profile()
    if not profile:
        return False
    
    # Vérifier que le certificat utilisateur correspond
    if not verify_user_certificate():
        return False
    
    return True
