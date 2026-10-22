"""Thème et composants réutilisables (style moderne, clair/sombre)."""
import logging
import os
import queue
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image

from modules.i18n import LANGS, get_lang, t
from modules.paths import client_dir, resource_path, safe_name

tr = t   # raccourci pour les vues : c.tr("texte {x}", x=1)


def _install_i18n():
    """Traduit automatiquement les textes des widgets ; les valeurs logiques restent en français."""
    if getattr(ctk, "_i18n_installed", False):
        return
    ctk._i18n_installed = True

    def tr_kw(k, keys):
        for key in keys:
            if isinstance(k.get(key), str):
                k[key] = t(k[key])
        return k

    def text_cls(base):
        class W(base):
            def __init__(self, *a, **k):
                super().__init__(*a, **tr_kw(k, ("text", "placeholder_text")))

            def configure(self, require_redraw=False, **k):
                return super().configure(require_redraw=require_redraw, **tr_kw(k, ("text", "placeholder_text")))
        W.__name__ = base.__name__
        return W

    def choice_cls(base):
        class W(base):
            def __init__(self, *a, **k):
                self._i18n_map = {}
                if "values" in k:
                    k["values"] = self._tr_values(k["values"])
                if callable(k.get("command")):
                    k["command"] = self._wrap(k["command"])
                super().__init__(*a, **k)

            def _tr_values(self, vals):
                out = []
                for v in vals:
                    d = t(v)
                    self._i18n_map[d] = v
                    out.append(d)
                return out

            def _wrap(self, cmd):
                return lambda d: cmd(self._i18n_map.get(d, d))

            def configure(self, require_redraw=False, **k):
                if "values" in k:
                    k["values"] = self._tr_values(k["values"])
                if callable(k.get("command")):
                    k["command"] = self._wrap(k["command"])
                return super().configure(require_redraw=require_redraw, **k)

            def get(self):
                d = super().get()
                return self._i18n_map.get(d, d)

            def set(self, v, *a, **k):
                return super().set(t(v), *a, **k)
        W.__name__ = base.__name__
        return W

    for name in ("CTkLabel", "CTkButton", "CTkEntry", "CTkCheckBox", "CTkSwitch"):
        setattr(ctk, name, text_cls(getattr(ctk, name)))
    for name in ("CTkComboBox", "CTkSegmentedButton"):
        setattr(ctk, name, choice_cls(getattr(ctk, name)))

    class TV(ctk.CTkTabview):
        def add(self, name):
            return super().add(t(name))

        def tab(self, name):
            return super().tab(t(name))

        def set(self, name):
            return super().set(t(name))

    class DLG(ctk.CTkInputDialog):
        def __init__(self, *a, **k):
            super().__init__(*a, **tr_kw(k, ("text", "title")))

    ctk.CTkTabview, ctk.CTkInputDialog = TV, DLG


_install_i18n()

ACCENT = ("#1F5FBF", "#3B82F6")
ACCENT_HOVER = ("#174A94", "#2563EB")
BG = ("#F3F5F9", "#12161C")
CARD = ("#FFFFFF", "#1B212B")
BORDER = ("#E2E6EE", "#2A3240")
TEXT = ("#111827", "#F3F4F6")
MUTED = ("#6B7280", "#9CA3AF")
DANGER = ("#DC2626", "#EF4444")
SUCCESS = ("#16A34A", "#22C55E")
SOFT = ("#EAF1FC", "#222C3B")

CONTACTS = [("+240 222 886 007", "240222886007"), ("+240 555 593 398", "240555593398"),
            ("+240 555 445 514", "240555445514")]
CONTACT_LINE = "WhatsApp : " + "  •  ".join(n for n, _ in CONTACTS)
TAGLINE = "Agence d'Architecture • Design • Innovation"
FONT = "Segoe UI"


def logo_image(width: int):
    img = Image.open(resource_path("assets/logo.jpg")).convert("RGB")
    h = int(img.height * width / img.width)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(width, h))


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14, border_width=1, border_color=BORDER, **kw)


def title(parent, text, size=24):
    return ctk.CTkLabel(parent, text=text, font=(FONT, size, "bold"), text_color=TEXT, anchor="w")


def subtitle(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text, font=(FONT, 13), text_color=MUTED, anchor="w",
                        justify="left", **kw)


def label(parent, text, bold=False, size=13, color=TEXT, **kw):
    return ctk.CTkLabel(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                        text_color=color, anchor="w", **kw)


def primary_btn(parent, text, command, width=160, **kw):
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=40, corner_radius=10,
                         fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
                         font=(FONT, 13, "bold"), **kw)


def ghost_btn(parent, text, command, width=140, danger=False, **kw):
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=40, corner_radius=10,
                         fg_color="transparent", border_width=1, border_color=BORDER,
                         hover_color=SOFT, text_color=DANGER if danger else TEXT,
                         font=(FONT, 13), **kw)


def entry(parent, placeholder="", width=240, show=None, **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, height=38, corner_radius=8,
                        border_color=BORDER, fg_color=("#FFFFFF", "#12161C"), font=(FONT, 13),
                        show=show, **kw)


def labeled_entry(parent, text, placeholder="", width=240, show=None):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    label(box, text, bold=True, size=12, color=MUTED).pack(anchor="w", pady=(0, 3))
    e = entry(box, placeholder, width, show)
    e.pack(anchor="w", fill="x")
    return box, e


def info(msg, title_="Information"):
    messagebox.showinfo(t(title_), t(msg))


def error(msg, title_="Une erreur est survenue"):
    messagebox.showerror(t(title_), t(msg))


def confirm(msg, title_="Confirmation"):
    return messagebox.askyesno(t(title_), t(msg))


def open_path(path):
    """Ouvre un fichier ou dossier avec l'application par défaut du système."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        error("Impossible d'ouvrir ce fichier.")


def copy_to_clipboard(widget, text):
    widget.clipboard_clear()
    widget.clipboard_append(text)


def run_bg(widget, func, done):
    """Exécute func() hors de l'interface (pas de gel) puis appelle done(ok, résultat)."""
    q = queue.Queue()

    def work():
        try:
            q.put((True, func()))
        except Exception as e:  # noqa: BLE001
            q.put((False, e))

    threading.Thread(target=work, daemon=True).start()

    def poll():
        try:
            ok, val = q.get_nowait()
        except queue.Empty:
            return widget.after(150, poll)
        done(ok, val)

    widget.after(150, poll)


def user_error(exc, default="L'opération a échoué. Vérifiez le fichier et réessayez."):
    """Affiche les erreurs de saisie (ValueError) ; journalise le reste sans détails techniques."""
    if isinstance(exc, ValueError):
        error(str(exc))
    else:
        logging.error("Erreur opération", exc_info=exc)
        error(default)


def parse_date(text):
    t = text.strip()
    if not t:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError("Date invalide : utilisez le format JJ/MM/AAAA.")


def fr_iso(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return ""


def unique_path(p):
    p = Path(p)
    n, cand = 2, p
    while cand.exists():
        cand = p.with_name(f"{p.stem}_{n}{p.suffix}")
        n += 1
    return cand


class OutputPicker(ctk.CTkFrame):
    """Choix de la destination : dossier d'un entrepreneur ou emplacement libre."""
    ASK = "Choisir à chaque enregistrement"

    def __init__(self, parent, db, text="Enregistrer dans :"):
        super().__init__(parent, fg_color="transparent")
        self.db, self.clients = db, {}
        label(self, text, bold=True, size=12, color=MUTED).pack(side="left", padx=(0, 8))
        self.cb = ctk.CTkComboBox(self, values=[self.ASK], width=250, height=36, state="readonly")
        self.cb.pack(side="left")
        self.refresh()

    def refresh(self):
        self.clients = {cl["name"]: cl for cl in self.db.list_clients()}
        cur = self.cb.get()
        self.cb.configure(values=[self.ASK] + list(self.clients))
        if cur not in self.clients:
            self.cb.set(self.ASK)

    def client(self):
        return self.clients.get(self.cb.get())

    def target(self, default_name, sub):
        """Chemin du fichier à écrire (None si annulé)."""
        cl = self.client()
        name = Path(default_name)
        if cl:
            return unique_path(client_dir(cl["name"], sub) / (safe_name(name.stem) + name.suffix.lower()))
        f = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=name.suffix,
                                         filetypes=[(name.suffix.upper().lstrip("."), "*" + name.suffix)])
        return Path(f) if f else None

    def folder(self, sub):
        cl = self.client()
        if cl:
            return client_dir(cl["name"], sub)
        f = filedialog.askdirectory(title="Choisissez le dossier de destination")
        return Path(f) if f else None


def lang_selector(parent, width=150):
    """Sélecteur FR / ES / EN (langue d'un document), initialisé sur la langue de l'application."""
    seg = ctk.CTkSegmentedButton(parent, values=[x.upper() for x in LANGS], width=width, height=34,
                                 selected_color=ACCENT, selected_hover_color=ACCENT_HOVER)
    seg.set(get_lang().upper())
    return seg


def lang_code(seg):
    return seg.get().lower()
