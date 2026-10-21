"""Base SQLite locale : compte admin, entrepreneurs tiers, historique des documents."""
import sqlite3
import time
from datetime import datetime

from .paths import app_data_dir
from .security import hash_password, verify_password

MAX_FAILED = 5
LOCK_SECONDS = 300


class Database:
    def __init__(self):
        self.path = app_data_dir() / "secretariat.db"
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def init(self):
        c = self.conn
        c.executescript("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL, pwd_hash TEXT NOT NULL, salt TEXT NOT NULL,
            iterations INTEGER NOT NULL, must_change INTEGER NOT NULL DEFAULT 1,
            failed INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS clients(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            logo_path TEXT DEFAULT '', address TEXT DEFAULT '', phone TEXT DEFAULT '',
            email TEXT DEFAULT '', nif TEXT DEFAULT '', rccm TEXT DEFAULT '',
            currency TEXT DEFAULT 'FCFA', tax_rate REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS activations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, activated_at TEXT NOT NULL,
            days INTEGER NOT NULL, mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
            doc_type TEXT NOT NULL, number TEXT NOT NULL UNIQUE, issue_date TEXT NOT NULL,
            final_client TEXT NOT NULL, total REAL NOT NULL, currency TEXT NOT NULL,
            pdf_path TEXT NOT NULL);
        """)
        if not c.execute("SELECT 1 FROM admin").fetchone():
            h, s, it = hash_password("Admin@1234")
            c.execute("INSERT INTO admin(id,username,pwd_hash,salt,iterations,must_change) VALUES(1,?,?,?,?,1)",
                      ("admin", h, s, it))
        c.commit()

    # ------------------------------------------------------------------- admin
    def authenticate(self, username: str, password: str):
        """Retourne (ok, message, must_change)."""
        row = self.conn.execute("SELECT * FROM admin WHERE id=1").fetchone()
        now = time.time()
        if row["locked_until"] > now:
            wait = int(row["locked_until"] - now) // 60 + 1
            return False, f"Trop de tentatives. Réessayez dans {wait} min.", False
        ok = (username.strip().lower() == row["username"]
              and verify_password(password, row["pwd_hash"], row["salt"], row["iterations"]))
        if ok:
            self.conn.execute("UPDATE admin SET failed=0, locked_until=0 WHERE id=1")
            self.conn.commit()
            return True, "", bool(row["must_change"])
        failed = row["failed"] + 1
        locked = now + LOCK_SECONDS if failed >= MAX_FAILED else 0
        self.conn.execute("UPDATE admin SET failed=?, locked_until=? WHERE id=1",
                          (0 if locked else failed, locked))
        self.conn.commit()
        return False, "Identifiant ou mot de passe incorrect.", False

    def change_password(self, new_password: str):
        h, s, it = hash_password(new_password)
        self.conn.execute("UPDATE admin SET pwd_hash=?, salt=?, iterations=?, must_change=0 WHERE id=1",
                          (h, s, it))
        self.conn.commit()

    def log_activation(self, days, mode="admin-local"):
        self.conn.execute("INSERT INTO activations(activated_at,days,mode) VALUES(datetime('now','localtime'),?,?)",
                          (int(days), mode))
        self.conn.commit()

    # ---------------------------------------------------------------- réglages
    def get_setting(self, key, default=""):
        r = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                          "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
        self.conn.commit()

    # ----------------------------------------------------------------- clients
    def list_clients(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM clients ORDER BY name COLLATE NOCASE")]

    def get_client(self, client_id):
        r = self.conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
        return dict(r) if r else None

    def save_client(self, d: dict):
        fields = ("name", "logo_path", "address", "phone", "email", "nif", "rccm", "currency", "tax_rate")
        vals = [d.get(f, "") for f in fields]
        if d.get("id"):
            self.conn.execute(
                "UPDATE clients SET name=?,logo_path=?,address=?,phone=?,email=?,nif=?,rccm=?,currency=?,tax_rate=? WHERE id=?",
                vals + [d["id"]])
            cid = d["id"]
        else:
            cur = self.conn.execute(
                "INSERT INTO clients(name,logo_path,address,phone,email,nif,rccm,currency,tax_rate) VALUES(?,?,?,?,?,?,?,?,?)",
                vals)
            cid = cur.lastrowid
        self.conn.commit()
        return cid

    def delete_client(self, client_id):
        self.conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        self.conn.commit()

    # --------------------------------------------------------------- documents
    def next_number(self, prefix: str) -> str:
        year = datetime.now().year
        pat = f"{prefix}-{year}-"
        rows = self.conn.execute("SELECT number FROM documents WHERE number LIKE ?", (pat + "%",)).fetchall()
        seq = max([int(r["number"].rsplit("-", 1)[1]) for r in rows] or [0]) + 1
        return f"{pat}{seq:04d}"

    def add_document(self, client_id, doc_type, number, issue_date, final_client, total, currency, pdf_path):
        self.conn.execute(
            "INSERT INTO documents(client_id,doc_type,number,issue_date,final_client,total,currency,pdf_path) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (client_id, doc_type, number, issue_date, final_client, float(total), currency, str(pdf_path)))
        self.conn.commit()

    def list_documents(self, client_id=None, limit=200):
        q = ("SELECT d.*, c.name AS client_name FROM documents d JOIN clients c ON c.id=d.client_id "
             + ("WHERE d.client_id=? " if client_id else "") + "ORDER BY d.id DESC LIMIT ?")
        args = ([client_id] if client_id else []) + [limit]
        return [dict(r) for r in self.conn.execute(q, args)]

    def stats(self):
        r = self.conn.execute(
            "SELECT (SELECT COUNT(*) FROM clients) AS clients, "
            "(SELECT COUNT(*) FROM documents) AS docs, "
            "(SELECT COUNT(*) FROM documents WHERE strftime('%Y-%m',issue_date)=strftime('%Y-%m','now','localtime')) AS month_docs"
        ).fetchone()
        return dict(r)
