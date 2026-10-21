"""Modèles intelligents : détection automatique des champs d'un document Word / texte."""
from datetime import date
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules import doc_template
from modules.paths import client_dir, safe_name
from . import common as c


class TemplatesView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.src, self.entries, self.clients = "", {}, {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        c.title(self, "Modèles de documents").grid(row=0, column=0, sticky="w")
        top = c.card(self)
        top.grid(row=1, column=0, sticky="ew", pady=12)
        top.grid_columnconfigure(1, weight=1)
        c.primary_btn(top, "1. Choisir un modèle", self.pick, width=190).grid(row=0, column=0, padx=14, pady=14)
        self.file_lbl = c.subtitle(top, "Word (.docx) ou texte (.txt) contenant des [Champs] ou « Libellé : ______ »")
        self.file_lbl.grid(row=0, column=1, sticky="w")
        self.client_cb = ctk.CTkComboBox(top, values=[""], width=230, height=38)
        self.client_cb.grid(row=0, column=2, padx=14)
        self.form = ctk.CTkScrollableFrame(self, fg_color=c.CARD, corner_radius=14, border_width=1, border_color=c.BORDER)
        self.form.grid(row=2, column=0, sticky="nsew")
        self.form.grid_columnconfigure((0, 1), weight=1, uniform="f")
        self.placeholder = c.subtitle(self.form, "Les champs détectés apparaîtront ici.")
        self.placeholder.grid(row=0, column=0, padx=16, pady=16, sticky="w")
        self.gen_btn = c.primary_btn(self, "2. Générer le document", self.generate, width=240)
        self.gen_btn.grid(row=3, column=0, sticky="e", pady=12)
        self.refresh()

    def refresh(self):
        self.clients = {cl["name"]: cl for cl in self.db.list_clients()}
        names = list(self.clients) or [""]
        self.client_cb.configure(values=names)
        if self.client_cb.get() not in self.clients:
            self.client_cb.set(names[0])

    def pick(self):
        f = filedialog.askopenfilename(filetypes=[("Modèles", "*.docx *.txt")])
        if not f:
            return
        try:
            fields = doc_template.detect_fields(f)
        except Exception:
            return c.error("Ce fichier n'a pas pu être lu. Vérifiez qu'il s'agit d'un .docx ou .txt valide.")
        self.src = f
        self.file_lbl.configure(text=Path(f).name, text_color=c.TEXT)
        for w in self.form.winfo_children():
            w.destroy()
        self.entries = {}
        if not fields:
            return c.subtitle(self.form, "Aucun champ détecté. Utilisez [NomClient] ou « Intitulé : ______ ».").grid(
                row=0, column=0, padx=16, pady=16)
        for i, fld in enumerate(fields):
            box, e = c.labeled_entry(self.form, fld["label"], width=240)
            box.grid(row=i // 2, column=i % 2, sticky="ew", padx=12, pady=6)
            self.entries[fld["id"]] = e

    def generate(self):
        cl = self.clients.get(self.client_cb.get())
        if not self.src or not self.entries:
            return c.error("Choisissez d'abord un modèle contenant des champs.")
        if not cl:
            return c.error("Sélectionnez un entrepreneur (onglet « Entrepreneurs »).")
        values = {k: e.get().strip() for k, e in self.entries.items()}
        first = next((v for v in values.values() if v), "document")
        name = f"{date.today().isoformat()}_{safe_name(Path(self.src).stem)}_{safe_name(first, maxlen=30)}{Path(self.src).suffix.lower()}"
        try:
            dest = doc_template.fill_template(self.src, client_dir(cl["name"], "Documents_Generes") / name, values)
        except Exception:
            return c.error("La génération a échoué. Fermez le fichier s'il est ouvert dans Word et réessayez.")
        if c.confirm(f"Document enregistré dans le dossier de {cl['name']}.\nL'ouvrir maintenant ?", "Terminé"):
            c.open_path(dest)
