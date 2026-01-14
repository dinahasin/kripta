from __future__ import annotations

"""
Bootstrap de sécurité pour Kripta.

- Gère le premier contact avec l'application (création du profil de sécurité)
- Stocke un mot de passe maître chiffré
- Génère une clé de récupération optionnelle, chiffrée avec un certificat connu uniquement de l'application
- Utilise Protobuf (schéma à définir) pour stocker le profil de sécurité sur disque
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import time
import getpass
import shutil

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.x509 import DNSName, SubjectAlternativeName
from cryptography.x509.oid import NameOID
import base64
import struct
import secrets
import datetime

from src.core.config import (
    SECURITY_DIR,
    SECURITY_PROFILE_FILE,
    APP_CERT_FILE,
    USER_CERT_FILE,
    PASSWORDS_DIR,
)

# Mot de passe pour chiffrer la clé privée de l'application (en pratique,
# il devra être compilé/obfusqué dans l'application finale)
APP_CERT_PASSWORD = b"change-this-in-build"


@dataclass
class SecurityProfileData:
    """
    Représentation en mémoire du profil de sécurité.

    Cette structure sera mappée vers un message Protobuf (voir security_profile.proto).
    """

    master_password_salt: bytes
    master_password_hash: bytes
    has_recovery_key: bool
    encrypted_recovery_key: Optional[bytes]
    created_at: int
    updated_at: int
    username: str  # Nom d'utilisateur Windows


def _hash_master_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Hash simplifié du mot de passe maître.

    NOTE: Pour une version production, utiliser Argon2 / scrypt / PBKDF2
    avec des paramètres forts. Ici on utilise SHA-256 + sel pour rester simple.
    """

    from hashlib import pbkdf2_hmac

    if salt is None:
        salt = secrets.token_bytes(16)

    dk = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt, dk


def _ensure_app_certificate() -> rsa.RSAPrivateKey:
    """
    S'assure qu'un certificat applicatif existe et renvoie la clé privée.

    Ce certificat est utilisé pour chiffrer/déchiffrer la clé de récupération.
    """

    if APP_CERT_FILE.exists():
        with open(APP_CERT_FILE, "rb") as f:
            pem_data = f.read()

        # Extraire clé privée
        private_key = serialization.load_pem_private_key(
            pem_data,
            password=APP_CERT_PASSWORD,
        )
        return private_key

    # Générer une nouvelle paire de clés RSA + certificat auto-signé
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "Kripta App Certificate"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Kripta"),
        ]
    )

    # Utiliser un identifiant pseudo-unique dans le SAN (pas lié à la machine)
    fingerprint_str = base64.urlsafe_b64encode(os.urandom(16)).decode("ascii").rstrip("=")
    alt_names = [DNSName(fingerprint_str)]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=3650)
        )
        .add_extension(SubjectAlternativeName(alt_names), critical=False)
        .sign(private_key, hashes.SHA256())
    )

    with open(APP_CERT_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(APP_CERT_PASSWORD),
            )
        )
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return private_key


def _ensure_user_certificate(username: str) -> rsa.RSAPrivateKey:
    """
    Génère ou charge un certificat utilisateur lié au nom d'utilisateur.
    
    Ce certificat permet de vérifier que les données correspondent bien à l'utilisateur.
    """
    if USER_CERT_FILE.exists():
        with open(USER_CERT_FILE, "rb") as f:
            pem_data = f.read()
        
        # Vérifier que le certificat correspond à l'utilisateur
        cert_start = pem_data.find(b"-----BEGIN CERTIFICATE-----")
        if cert_start != -1:
            cert_pem = pem_data[cert_start:]
            cert = x509.load_pem_x509_certificate(cert_pem)
            
            # Vérifier le CN (Common Name) correspond au nom d'utilisateur
            cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            if cn != username:
                # L'utilisateur a changé, régénérer
                USER_CERT_FILE.unlink()
            else:
                # Charger la clé privée
                private_key = serialization.load_pem_private_key(
                    pem_data,
                    password=APP_CERT_PASSWORD,
                )
                return private_key
    
    # Générer un nouveau certificat utilisateur
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, username),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Kripta User"),
    ])
    
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=3650)
        )
        .sign(private_key, hashes.SHA256())
    )
    
    with open(USER_CERT_FILE, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(APP_CERT_PASSWORD),
            )
        )
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    return private_key


def verify_user_certificate() -> bool:
    """
    Vérifie que le certificat utilisateur correspond au nom d'utilisateur actuel.
    """
    if not USER_CERT_FILE.exists():
        return False
    
    try:
        current_username = getpass.getuser()
        with open(USER_CERT_FILE, "rb") as f:
            pem_data = f.read()
        
        cert_start = pem_data.find(b"-----BEGIN CERTIFICATE-----")
        if cert_start == -1:
            return False
        
        cert_pem = pem_data[cert_start:]
        cert = x509.load_pem_x509_certificate(cert_pem)
        
        cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        return cn == current_username
    except Exception:
        return False


def _load_app_keys() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = _ensure_app_certificate()
    return private_key, private_key.public_key()


def encrypt_with_app_cert(plaintext: bytes) -> bytes:
    """
    Chiffre des données arbitraires de façon hybride (RSA + AES-GCM)
    en utilisant le certificat applicatif.

    Seule l'application (qui possède la clé privée) peut déchiffrer.
    """

    _, public_key = _load_app_keys()
    cek = os.urandom(32)  # Clé de session AES
    nonce = os.urandom(12)
    ciphertext = AESGCM(cek).encrypt(nonce, plaintext, None)

    wrapped_key = public_key.encrypt(
        cek,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    token = b"V2" + struct.pack(">I", len(wrapped_key)) + wrapped_key + nonce + ciphertext
    return base64.urlsafe_b64encode(token)


def decrypt_with_app_cert(encrypted_token: bytes) -> bytes:
    """
    Déchiffre des données chiffrées avec encrypt_with_app_cert().
    """

    private_key, _ = _load_app_keys()
    blob = base64.urlsafe_b64decode(encrypted_token)

    if not blob.startswith(b"V2"):
        raise ValueError("Version inconnue")

    ofs = 2
    (wrapped_len,) = struct.unpack(">I", blob[ofs : ofs + 4])
    ofs += 4
    wrapped_key = blob[ofs : ofs + wrapped_len]
    ofs += wrapped_len
    nonce = blob[ofs : ofs + 12]
    ofs += 12
    ciphertext = blob[ofs:]

    cek = private_key.decrypt(
        wrapped_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return AESGCM(cek).decrypt(nonce, ciphertext, None)


def initialize_security_profile(
    master_password: str,
    recovery_key: Optional[bytes] = None,
) -> SecurityProfileData:
    """
    Initialise le profil de sécurité à la première ouverture de l'application.

    - Hash le mot de passe maître
    - Génère ou vérifie le certificat utilisateur (basé sur le nom d'utilisateur)
    - Chiffre (optionnellement) une clé de récupération que l'utilisateur pourra
      stocker où il veut (fichier, clé USB, etc.)
    - Prépare une structure qui sera sérialisée en Protobuf sur disque
    """

    # Obtenir le nom d'utilisateur et générer/verifier le certificat utilisateur
    username = getpass.getuser()
    _ensure_user_certificate(username)

    salt, pwd_hash = _hash_master_password(master_password)
    now = int(time.time())

    encrypted_recovery: Optional[bytes] = None
    has_recovery = False

    if recovery_key:
        encrypted_recovery = encrypt_with_app_cert(recovery_key)
        has_recovery = True

    profile = SecurityProfileData(
        master_password_salt=salt,
        master_password_hash=pwd_hash,
        has_recovery_key=has_recovery,
        encrypted_recovery_key=encrypted_recovery,
        created_at=now,
        updated_at=now,
        username=username,
    )

    # Sérialiser en Protobuf
    from src.security.profile_protobuf import _save_security_profile
    _save_security_profile(profile)

    return profile


def verify_master_password(profile: SecurityProfileData, password: str) -> bool:
    """
    Vérifie un mot de passe par rapport au profil chargé.
    """

    _, candidate_hash = _hash_master_password(password, salt=profile.master_password_salt)
    return secrets.compare_digest(candidate_hash, profile.master_password_hash)


def decrypt_recovery_key(profile: SecurityProfileData) -> Optional[bytes]:
    """
    Déchiffre la clé de récupération à partir du profil.
    """

    if not profile.has_recovery_key or not profile.encrypted_recovery_key:
        return None

    return decrypt_with_app_cert(profile.encrypted_recovery_key)


def import_recovery_key_file(file_path: Path) -> Optional[bytes]:
    """
    Importe une clé de récupération depuis un fichier.
    
    Args:
        file_path: Chemin vers le fichier contenant la clé chiffrée
    
    Returns:
        bytes: Clé de récupération déchiffrée, ou None si échec
    """
    try:
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
        
        # Tenter de déchiffrer
        return decrypt_with_app_cert(encrypted_data)
    except Exception:
        return None


def load_security_profile() -> Optional[SecurityProfileData]:
    """
    Charge le profil de sécurité depuis le fichier.
    """
    from src.security.profile_protobuf import _load_security_profile
    return _load_security_profile()


def reset_security_state() -> None:
    """
    Supprime toutes les données de sécurité locales :
    - Profil de sécurité (mot de passe maître, métadonnées)
    - Certificat applicatif et certificat utilisateur
    - Clés de récupération enregistrées
    - Dossier des mots de passe chiffrés
    """
    # Supprimer fichiers critiques
    targets = [
        SECURITY_PROFILE_FILE,
        APP_CERT_FILE,
        USER_CERT_FILE,
        SECURITY_DIR / "recovery_key.kripta",
    ]
    for path in targets:
        try:
            if path.exists():
                path.unlink()
        except Exception:
            # On ignore les erreurs individuelles pour ne pas bloquer l'utilisateur
            pass

    # Nettoyer le dossier des mots de passe
    try:
        if PASSWORDS_DIR.exists():
            for item in PASSWORDS_DIR.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink(missing_ok=True)
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
    except Exception:
        pass