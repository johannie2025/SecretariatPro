"""Sauvegarde / restauration (base de données + dossier Data_Secretariat)."""
import sqlite3
import tempfile
import zipfile
from pathlib import Path

from .paths import data_root

DB_NAME = "secretariat.db"


def make_backup(db, dest_zip) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        snap = Path(tmp) / DB_NAME
        dst = sqlite3.connect(snap)
        db.conn.backup(dst)           # copie cohérente même base ouverte
        dst.close()
        root = data_root()
        with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(snap, DB_NAME)
            for f in root.rglob("*"):
                if f.is_file():
                    z.write(f, "Data_Secretariat/" + f.relative_to(root).as_posix())
    return Path(dest_zip)


def restore_backup(db, src_zip):
    root = data_root().resolve()
    with zipfile.ZipFile(src_zip) as z:
        names = z.namelist()
        if DB_NAME not in names:
            raise ValueError("Ce fichier n'est pas une sauvegarde SecretariatPro.")
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(z.extract(DB_NAME, tmp))
            check = sqlite3.connect(snap)
            try:
                if not check.execute("SELECT 1 FROM admin LIMIT 1").fetchone():
                    raise ValueError("Sauvegarde invalide.")
                check.backup(db.conn)
            except sqlite3.DatabaseError:
                raise ValueError("Sauvegarde invalide ou endommagée.")
            finally:
                check.close()
        for n in names:
            if not n.startswith("Data_Secretariat/") or n.endswith("/"):
                continue
            target = (root / n[len("Data_Secretariat/"):]).resolve()
            if root not in target.parents:          # anti « zip slip »
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as s, open(target, "wb") as d:
                d.write(s.read())
    db.init()
