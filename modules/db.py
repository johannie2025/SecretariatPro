"""Base SQLite locale : compte admin, entrepreneurs tiers, historique des documents."""
import re
import sqlite3
import time
from datetime import datetime

from .paths import app_data_dir
from .security import PBKDF2_ITERATIONS, hash_password, password_policy_error, verify_password

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
ROLES = ("admin", "secretariat")
MAX_FAILED = 5
LOCK_SECONDS = 300


class Database:
    def __init__(self):
        self.path = app_data_dir() / "secretariat.db"
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.current_user = None

    def init(self):
        c = self.conn
        c.executescript("""
        CREATE TABLE IF NOT EXISTS admin(
            id INTEGER PRIMARY KEY CHECK (id = 1),
            username TEXT NOT NULL, pwd_hash TEXT NOT NULL, salt TEXT NOT NULL,
            iterations INTEGER NOT NULL, must_change INTEGER NOT NULL DEFAULT 1,
            failed INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            role TEXT NOT NULL CHECK(role IN ('admin','secretariat')), pwd_hash TEXT NOT NULL, salt TEXT NOT NULL,
            iterations INTEGER NOT NULL, must_change INTEGER NOT NULL DEFAULT 1, failed INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS clients(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            logo_path TEXT DEFAULT '', address TEXT DEFAULT '', phone TEXT DEFAULT '',
            email TEXT DEFAULT '', nif TEXT DEFAULT '', rccm TEXT DEFAULT '',
            currency TEXT DEFAULT 'FCFA', tax_rate REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS activations(
            id INTEGER PRIMARY KEY AUTOINCREMENT, activated_at TEXT NOT NULL,
            days INTEGER NOT NULL, mode TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS mails(
            id INTEGER PRIMARY KEY AUTOINCREMENT, direction TEXT NOT NULL, ref TEXT NOT NULL UNIQUE,
            mail_date TEXT NOT NULL, party TEXT NOT NULL, subject TEXT NOT NULL,
            client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'À traiter', file_path TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, due_date TEXT DEFAULT '',
            done INTEGER NOT NULL DEFAULT 0, client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL);
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
        if not c.execute("SELECT 1 FROM users").fetchone():      # migration de l'ancien compte unique
            old = c.execute("SELECT * FROM admin WHERE id=1").fetchone()
            c.execute("INSERT INTO users(username,role,pwd_hash,salt,iterations,must_change,failed,locked_until) "
                      "VALUES(?,?,?,?,?,?,?,?)", (old["username"], "admin", old["pwd_hash"], old["salt"],
                                                  old["iterations"], old["must_change"], old["failed"], old["locked_until"]))
        c.commit()

    # ------------------------------------------------------------------- comptes
    def is_admin(self):
        return bool(self.current_user and self.current_user["role"] == "admin")

    def authenticate(self, username: str, password: str):
        """Retourne (ok, message, must_change) et mémorise l'utilisateur connecté."""
        self.current_user = None
        row = self.conn.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
        now = time.time()
        if row is None:
            verify_password(password, "0" * 64, "00" * 32, PBKDF2_ITERATIONS)   # même durée : pas de fuite d'info
            return False, "Identifiant ou mot de passe incorrect.", False
        if not row["active"]:
            return False, "Ce compte est désactivé. Contactez l'administrateur.", False
        if row["locked_until"] > now:
            wait = int(row["locked_until"] - now) // 60 + 1
            return False, f"Trop de tentatives. Réessayez dans {wait} min.", False
        if verify_password(password, row["pwd_hash"], row["salt"], row["iterations"]):
            self.conn.execute("UPDATE users SET failed=0, locked_until=0 WHERE id=?", (row["id"],))
            self.conn.commit()
            self.current_user = {"id": row["id"], "username": row["username"], "role": row["role"]}
            return True, "", bool(row["must_change"])
        failed = row["failed"] + 1
        locked = now + LOCK_SECONDS if failed >= MAX_FAILED else 0
        self.conn.execute("UPDATE users SET failed=?, locked_until=? WHERE id=?", (0 if locked else failed, locked, row["id"]))
        self.conn.commit()
        return False, "Identifiant ou mot de passe incorrect.", False

    def change_password(self, new_password: str):
        if not self.current_user:
            raise ValueError("Identifiant ou mot de passe incorrect.")
        h, s, it = hash_password(new_password)
        self.conn.execute("UPDATE users SET pwd_hash=?, salt=?, iterations=?, must_change=0 WHERE id=?",
                          (h, s, it, self.current_user["id"]))
        self.conn.commit()

    def log_activation(self, days, mode="admin-local"):
        self.conn.execute("INSERT INTO activations(activated_at,days,mode) VALUES(datetime('now','localtime'),?,?)",
                          (int(days), mode))
        self.conn.commit()

    def list_users(self):
        return [dict(r) for r in self.conn.execute("SELECT id,username,role,active FROM users ORDER BY role, username")]

    def create_user(self, username, password, role):
        username = username.strip()
        if not USERNAME_RE.match(username):
            raise ValueError("Nom d'utilisateur invalide (3 à 30 caractères : lettres, chiffres, . _ -).")
        if role not in ROLES:
            raise ValueError("Rôle invalide.")
        err = password_policy_error(password)
        if err:
            raise ValueError(err)
        h, s, it = hash_password(password)
        try:
            self.conn.execute("INSERT INTO users(username,role,pwd_hash,salt,iterations,must_change) VALUES(?,?,?,?,?,1)",
                              (username, role, h, s, it))
        except sqlite3.IntegrityError:
            raise ValueError("Ce nom d'utilisateur existe déjà.")
        self.conn.commit()

    def reset_password(self, user_id, new_password):
        err = password_policy_error(new_password)
        if err:
            raise ValueError(err)
        h, s, it = hash_password(new_password)
        self.conn.execute("UPDATE users SET pwd_hash=?, salt=?, iterations=?, must_change=1, failed=0, locked_until=0 WHERE id=?",
                          (h, s, it, user_id))
        self.conn.commit()

    def _guard_user(self, user_id):
        if self.current_user and user_id == self.current_user["id"]:
            raise ValueError("Vous ne pouvez pas supprimer ou désactiver votre propre compte.")
        row = self.conn.execute("SELECT role, active FROM users WHERE id=?", (user_id,)).fetchone()
        if row and row["role"] == "admin" and row["active"]:
            others = self.conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1 AND id<>?", (user_id,)).fetchone()[0]
            if not others:
                raise ValueError("Il doit rester au moins un administrateur actif.")

    def set_user_active(self, user_id, active):
        if not active:
            self._guard_user(user_id)
        self.conn.execute("UPDATE users SET active=? WHERE id=?", (1 if active else 0, user_id))
        self.conn.commit()

    def delete_user(self, user_id):
        self._guard_user(user_id)
        self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))
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

    # ----------------------------------------------------------------- courrier
    def add_mail(self, direction, mail_date, party, subject, client_id=None, status="À traiter", file_path=""):
        if direction not in ("Entrant", "Sortant"):
            raise ValueError("Type de courrier invalide.")
        if not party.strip() or not subject.strip():
            raise ValueError("Indiquez le correspondant et l'objet.")
        prefix = "E" if direction == "Entrant" else "S"
        pat = f"{prefix}-{mail_date[:4]}-"
        rows = self.conn.execute("SELECT ref FROM mails WHERE ref LIKE ?", (pat + "%",)).fetchall()
        ref = f"{pat}{max([int(r['ref'].rsplit('-', 1)[1]) for r in rows] or [0]) + 1:04d}"
        self.conn.execute("INSERT INTO mails(direction,ref,mail_date,party,subject,client_id,status,file_path) "
                          "VALUES(?,?,?,?,?,?,?,?)",
                          (direction, ref, mail_date, party.strip(), subject.strip(), client_id, status, file_path))
        self.conn.commit()
        return ref

    def list_mails(self, search="", limit=300):
        like = f"%{search.strip()}%"
        return [dict(r) for r in self.conn.execute(
            "SELECT m.*, c.name AS client_name FROM mails m LEFT JOIN clients c ON c.id=m.client_id "
            "WHERE m.ref LIKE ? OR m.party LIKE ? OR m.subject LIKE ? OR IFNULL(c.name,'') LIKE ? "
            "ORDER BY m.mail_date DESC, m.id DESC LIMIT ?", (like, like, like, like, limit))]

    def set_mail_status(self, mail_id, status):
        self.conn.execute("UPDATE mails SET status=? WHERE id=?", (status, mail_id))
        self.conn.commit()

    def delete_mail(self, mail_id):
        self.conn.execute("DELETE FROM mails WHERE id=?", (mail_id,))
        self.conn.commit()

    # ------------------------------------------------------------------ tâches
    def add_task(self, title, due_date="", client_id=None):
        if not title.strip():
            raise ValueError("Indiquez la tâche à faire.")
        self.conn.execute("INSERT INTO tasks(title,due_date,client_id) VALUES(?,?,?)", (title.strip(), due_date, client_id))
        self.conn.commit()

    def list_tasks(self, show_done=False):
        q = ("SELECT t.*, c.name AS client_name FROM tasks t LEFT JOIN clients c ON c.id=t.client_id "
             + ("" if show_done else "WHERE t.done=0 ") + "ORDER BY t.done, (t.due_date=''), t.due_date, t.id")
        return [dict(r) for r in self.conn.execute(q)]

    def set_task_done(self, task_id, done):
        self.conn.execute("UPDATE tasks SET done=? WHERE id=?", (1 if done else 0, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def task_counts(self):
        r = self.conn.execute(
            "SELECT COALESCE(SUM(due_date<>'' AND due_date<date('now','localtime')),0) AS late, "
            "COALESCE(SUM(due_date=date('now','localtime')),0) AS today, COUNT(*) AS open "
            "FROM tasks WHERE done=0").fetchone()
        return dict(r)

    def stats(self):
        r = self.conn.execute(
            "SELECT (SELECT COUNT(*) FROM clients) AS clients, "
            "(SELECT COUNT(*) FROM documents) AS docs, "
            "(SELECT COUNT(*) FROM documents WHERE strftime('%Y-%m',issue_date)=strftime('%Y-%m','now','localtime')) AS month_docs"
        ).fetchone()
        return dict(r)
