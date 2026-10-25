"""Gestion des entrepreneurs tiers (profils marque blanche)."""
from tkinter import filedialog

import customtkinter as ctk

from modules import client_manager
from modules.paths import client_dir
from . import common as c


class ClientsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.current_id = None
        self.logo_path = ""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        c.title(self, "Entrepreneurs").grid(row=0, column=0, columnspan=2, sticky="w")

        left = c.card(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 14), pady=(12, 0))
        c.primary_btn(left, "+  Nouvel entrepreneur", self.new, width=250).pack(padx=14, pady=14)
        self.listbox = ctk.CTkScrollableFrame(left, fg_color="transparent", width=250)
        self.listbox.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        right = self.right = c.card(self)
        right.grid(row=1, column=1, sticky="nsew", pady=(12, 0))
        self.hint = c.card(self)
        self.hint.grid(row=1, column=1, sticky="nsew", pady=(12, 0))
        c.subtitle(self.hint, "Sélectionnez un entrepreneur dans la liste ou cliquez sur « + Nouvel entrepreneur ».",
                   wraplength=420).pack(padx=24, pady=40)
        form = ctk.CTkScrollableFrame(right, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=10, pady=10)
        form.grid_columnconfigure((0, 1), weight=1, uniform="f")
        self.fields = {}
        spec = [("name", "Nom de l'entreprise *", 0, 0, 2), ("address", "Adresse", 1, 0, 2),
                ("phone", "Téléphone", 2, 0, 1), ("email", "E-mail", 2, 1, 1),
                ("nif", "NIF", 3, 0, 1), ("rccm", "RCCM", 3, 1, 1),
                ("currency", "Devise (FCFA, EUR...)", 4, 0, 1), ("tax_rate", "Taxe / TVA par défaut (%)", 4, 1, 1)]
        for key, text, r, col, span in spec:
            box, e = c.labeled_entry(form, text, width=200)
            box.grid(row=r, column=col, columnspan=span, sticky="ew", padx=8, pady=6)
            self.fields[key] = e
        logo_row = ctk.CTkFrame(form, fg_color="transparent")
        logo_row.grid(row=5, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        c.ghost_btn(logo_row, "Choisir un logo...", self.pick_logo, width=170).pack(side="left")
        self.logo_lbl = c.subtitle(logo_row, "Aucun logo")
        self.logo_lbl.pack(side="left", padx=12)
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(0, 16))
        c.primary_btn(actions, "Enregistrer", self.save, width=150).pack(side="left")
        c.ghost_btn(actions, "Ouvrir le dossier", self.open_folder, width=150).pack(side="left", padx=8)
        c.ghost_btn(actions, "Supprimer", self.delete, width=120, danger=True).pack(side="right")
        self.refresh()
        self.show_hint()

    def refresh(self):
        for w in self.listbox.winfo_children():
            w.destroy()
        for cl in self.db.list_clients():
            ctk.CTkButton(self.listbox, text=cl["name"], anchor="w", height=38, corner_radius=8,
                          fg_color=c.SOFT if cl["id"] == self.current_id else "transparent",
                          hover_color=c.SOFT, text_color=c.TEXT, font=(c.FONT, 13),
                          command=lambda i=cl["id"]: self.load(i)).pack(fill="x", pady=2)

    def _fill(self, data):
        for k, e in self.fields.items():
            e.delete(0, "end")
            e.insert(0, str(data.get(k, "") if data.get(k) is not None else ""))
        self.logo_path = data.get("logo_path", "")
        self.logo_lbl.configure(text=self.logo_path.split("\\")[-1].split("/")[-1] or "Aucun logo")

    def show_hint(self):
        self.current_id = None
        self.right.grid_remove()
        self.hint.grid()
        self.refresh()

    def _show_form(self):
        self.hint.grid_remove()
        self.right.grid()

    def new(self):
        self.current_id = None
        self._fill({"currency": "FCFA", "tax_rate": "0"})
        self._show_form()
        self.refresh()

    def load(self, cid):
        self.current_id = cid
        self._fill(self.db.get_client(cid))
        self._show_form()
        self.refresh()

    def pick_logo(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if f:
            self.logo_path = f
            self.logo_lbl.configure(text=f.split("\\")[-1].split("/")[-1])

    def save(self):
        data = {k: e.get().strip() for k, e in self.fields.items()}
        data.update(id=self.current_id, logo_path=self.logo_path)
        try:
            self.current_id = client_manager.save(self.db, data)
        except ValueError as e:
            return c.error(str(e), "Vérifiez le formulaire")
        self.refresh()
        self.load(self.current_id)
        c.info("Entrepreneur enregistré.")

    def delete(self):
        if not self.current_id:
            return
        if c.confirm("Supprimer cet entrepreneur et son historique de documents ?\n"
                     "(Les fichiers PDF déjà créés restent sur votre ordinateur.)"):
            self.db.delete_client(self.current_id)
            self.show_hint()

    def open_folder(self):
        if self.current_id:
            c.open_path(client_dir(self.db.get_client(self.current_id)["name"]))
