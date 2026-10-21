"""Chemins, dossiers de données et nettoyage des noms (anti Path Traversal)."""
import os
import re
import sys
import unicodedata
from pathlib import Path

APP_NAME = "SecretariatPro"


def resource_path(rel: str) -> str:
    """Chemin d'une ressource (fonctionne en dev et dans l'exe PyInstaller)."""
    base = getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parent.parent
    return str(Path(base) / rel)


def app_data_dir() -> Path:
    """Dossier privé de l'application (base SQLite, licence chiffrée, logs)."""
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    p = Path(base) / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_root() -> Path:
    """Dossier visible par l'utilisateur : Documents/Data_Secretariat."""
    docs = Path.home() / "Documents"
    root = (docs if docs.exists() else Path.home()) / "Data_Secretariat"
    (root / "Clients").mkdir(parents=True, exist_ok=True)
    return root


def safe_name(value, default: str = "sans_nom", maxlen: int = 80) -> str:
    """Transforme n'importe quel texte en nom de fichier/dossier sûr."""
    v = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    v = re.sub(r"[^A-Za-z0-9._ -]", "_", v)
    v = re.sub(r"\s+", "_", v.strip(" ._"))
    v = re.sub(r"_+", "_", v).strip(" ._")
    return v[:maxlen] or default


def client_dir(client_name: str, sub: str | None = None) -> Path:
    """Dossier d'un entrepreneur tiers : Data_Secretariat/Clients/<Nom>/<sub>."""
    root = (data_root() / "Clients").resolve()
    base = (root / safe_name(client_name)).resolve()
    if root not in base.parents:
        raise ValueError("Chemin non autorisé.")
    target = base / safe_name(sub) if sub else base
    target.mkdir(parents=True, exist_ok=True)
    return target
