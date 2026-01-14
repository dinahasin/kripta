"""
Gestion de la configuration via .env
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Charger le .env s'il existe
load_dotenv()

# Dossier de base par défaut
DEFAULT_SECURITY_DIR = Path.home() / ".kripta"

# Récupération des chemins depuis .env ou valeurs par défaut
SECURITY_DIR = Path(os.getenv("KRIPTA_SECURITY_DIR", str(DEFAULT_SECURITY_DIR)))
SECURITY_DIR.mkdir(parents=True, exist_ok=True)

SECURITY_PROFILE_FILE = Path(
    os.getenv("KRIPTA_SECURITY_PROFILE_FILE", str(SECURITY_DIR / "security_profile.bin"))
)

PASSWORDS_DIR = Path(
    os.getenv("KRIPTA_PASSWORDS_DIR", str(SECURITY_DIR / "passwords"))
)
PASSWORDS_DIR.mkdir(parents=True, exist_ok=True)

APP_CERT_FILE = Path(
    os.getenv("KRIPTA_APP_CERT_FILE", str(SECURITY_DIR / "app_cert.pem"))
)

USER_CERT_FILE = Path(
    os.getenv("KRIPTA_USER_CERT_FILE", str(SECURITY_DIR / "user_cert.pem"))
)
