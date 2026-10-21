"""Sécurité : mots de passe (PBKDF2), empreinte machine (HWID), licence hors-ligne.

Licence : la clé est SIGNÉE par W Design (Ed25519, clé privée jamais incluse dans
l'application). Une fois activée, elle est stockée CHIFFRÉE en AES-256-GCM avec une
clé dérivée du HWID : copier le fichier sur un autre PC le rend inutilisable.
"""
import base64
import hashlib
import hmac
import json
import os
import platform
import re
import secrets
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .paths import app_data_dir

# Clé PUBLIQUE de vérification (la clé privée reste chez W Design).
LICENSE_PUBLIC_KEY_B64 = "fHqEYy5GR8cC06Gq99CljcshXfRw9We7CyIx0ycpX50="
PBKDF2_ITERATIONS = 600_000
VALID_DURATIONS = (30, 90, 180, 365)


# ----------------------------------------------------------------- mots de passe
def hash_password(password: str, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS):
    salt = salt or secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return digest.hex(), salt.hex(), iterations


def verify_password(password: str, hash_hex: str, salt_hex: str, iterations: int) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), iterations)
    return hmac.compare_digest(digest.hex(), hash_hex)


def password_policy_error(password: str) -> str | None:
    if len(password) < 10:
        return "Le mot de passe doit contenir au moins 10 caractères."
    if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password):
        return "Utilisez des majuscules et des minuscules."
    if not re.search(r"\d", password):
        return "Ajoutez au moins un chiffre."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Ajoutez au moins un symbole (@, #, !, ...)."
    if password == "Admin@1234":
        return "Choisissez un mot de passe différent de celui par défaut."
    return None


# ------------------------------------------------------------------------- HWID
def get_hwid() -> str:
    parts = []
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            ) as k:
                parts.append(str(winreg.QueryValueEx(k, "MachineGuid")[0]))
        except OSError:
            pass
    if not parts:  # repli (hors Windows ou registre inaccessible)
        try:
            with open("/etc/machine-id", encoding="ascii") as f:
                parts.append(f.read().strip())
        except OSError:
            parts.append(f"{uuid.getnode():012x}")
    parts += [platform.machine(), platform.processor()]
    h = hashlib.sha256("|".join(parts).encode()).hexdigest().upper()[:16]
    return "-".join(h[i:i + 4] for i in range(0, 16, 4))


# ---------------------------------------------------------------------- licence
@dataclass
class LicenseStatus:
    valid: bool
    reason: str = ""
    expires: date | None = None
    days_left: int = 0


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _license_file():
    return app_data_dir() / "license.dat"


def _aes(hwid: str) -> AESGCM:
    key = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"SecretariatPro-license-v1",
               info=b"aes-gcm").derive(hwid.encode())
    return AESGCM(key)


def _verify_key(key_str: str, hwid: str):
    try:
        prefix, p, s = re.sub(r"\s+", "", key_str).split(".")
        if prefix != "SP1":
            raise ValueError
        payload_b, sig = _b64d(p), _b64d(s)
        Ed25519PublicKey.from_public_bytes(base64.b64decode(LICENSE_PUBLIC_KEY_B64)).verify(sig, payload_b)
        payload = json.loads(payload_b)
    except Exception:
        return None, "Clé de licence invalide."
    if payload.get("hwid") != hwid:
        return None, "Cette clé n'a pas été émise pour cet ordinateur."
    if payload.get("days") not in VALID_DURATIONS:
        return None, "Durée de licence non reconnue."
    return payload, None


def _save_state(state: dict, hwid: str):
    nonce = secrets.token_bytes(12)
    blob = nonce + _aes(hwid).encrypt(nonce, json.dumps(state).encode(), b"SP-license")
    tmp = _license_file().with_suffix(".tmp")
    tmp.write_bytes(blob)
    os.replace(tmp, _license_file())


def _load_state(hwid: str):
    f = _license_file()
    if not f.exists():
        return None
    try:
        blob = f.read_bytes()
        return json.loads(_aes(hwid).decrypt(blob[:12], blob[12:], b"SP-license"))
    except Exception:
        return {"_corrupt": True}


def activate_license(key_str: str):
    hwid = get_hwid()
    payload, err = _verify_key(key_str, hwid)
    if err:
        return False, err
    state = _load_state(hwid) or {}
    if state.get("key_id") == payload.get("id"):
        return False, "Cette clé a déjà été utilisée sur cet ordinateur."
    now = time.time()
    # Une clé de renouvellement s'ajoute à la durée restante éventuelle.
    start = datetime.fromtimestamp(now).date()
    base = date.fromisoformat(state["expires"]) if state.get("expires") and not state.get("_corrupt") else start
    base = max(base, start)
    expires = base + timedelta(days=int(payload["days"]))
    _save_state({"key_id": payload.get("id"), "expires": expires.isoformat(), "last_seen": now}, hwid)
    return True, f"Licence activée jusqu'au {expires.strftime('%d/%m/%Y')}."


def activate_local(days: int):
    """Activation directe par l'administrateur sur CE poste (sans clé), liée au HWID."""
    if days not in VALID_DURATIONS:
        return False, "Durée de licence non reconnue."
    hwid = get_hwid()
    state = _load_state(hwid) or {}
    now = time.time()
    start = datetime.fromtimestamp(now).date()
    base = date.fromisoformat(state["expires"]) if state.get("expires") and not state.get("_corrupt") else start
    expires = max(base, start) + timedelta(days=days)
    _save_state({"key_id": "local-" + secrets.token_hex(4), "expires": expires.isoformat(), "last_seen": now}, hwid)
    return True, f"Licence activée jusqu'au {expires.strftime('%d/%m/%Y')}."


def check_license() -> LicenseStatus:
    hwid = get_hwid()
    state = _load_state(hwid)
    if state is None:
        return LicenseStatus(False, "Aucune licence activée sur cet ordinateur.")
    if state.get("_corrupt"):
        return LicenseStatus(False, "Fichier de licence invalide pour cet ordinateur.")
    now = time.time()
    if now < float(state.get("last_seen", 0)) - 86400:
        return LicenseStatus(False, "Date système incohérente : corrigez l'horloge de l'ordinateur.")
    expires = date.fromisoformat(state["expires"])
    today = datetime.fromtimestamp(now).date()
    if today > expires:
        return LicenseStatus(False, f"Licence expirée le {expires.strftime('%d/%m/%Y')}.", expires, 0)
    state["last_seen"] = max(now, float(state.get("last_seen", 0)))
    _save_state(state, hwid)
    return LicenseStatus(True, "", expires, (expires - today).days)
