"""Gestion des profils d'entrepreneurs tiers (marque blanche)."""
import shutil
from pathlib import Path

from .paths import client_dir

SUBFOLDERS = ("Factures_Emises", "Devis_Proforma", "Documents_Generes", "Documents_OCR", "Logo")
ALLOWED_LOGO = {".png", ".jpg", ".jpeg"}


def validate(data: dict) -> str | None:
    if not data.get("name", "").strip():
        return "Le nom de l'entreprise est obligatoire."
    try:
        t = float(str(data.get("tax_rate", 0) or 0).replace(",", "."))
        if not 0 <= t <= 100:
            raise ValueError
    except ValueError:
        return "Le taux de taxe doit être un nombre entre 0 et 100."
    return None


def save(db, data: dict) -> int:
    err = validate(data)
    if err:
        raise ValueError(err)
    data = dict(data)
    data["name"] = data["name"].strip()
    data["tax_rate"] = float(str(data.get("tax_rate", 0) or 0).replace(",", "."))
    data["currency"] = (data.get("currency") or "FCFA").strip().upper()[:6]
    # Copie du logo dans le dossier du client (le fichier d'origine peut disparaître).
    logo = data.get("logo_path", "")
    base = client_dir(data["name"])
    for sub in SUBFOLDERS:
        (base / sub).mkdir(exist_ok=True)
    if logo and Path(logo).is_file() and Path(logo).suffix.lower() in ALLOWED_LOGO:
        dest = base / "Logo" / ("logo" + Path(logo).suffix.lower())
        if Path(logo).resolve() != dest.resolve():
            shutil.copyfile(logo, dest)
        data["logo_path"] = str(dest)
    else:
        data["logo_path"] = ""
    try:
        return db.save_client(data)
    except Exception as e:
        if "UNIQUE" in str(e):
            raise ValueError("Un entrepreneur portant ce nom existe déjà.")
        raise
