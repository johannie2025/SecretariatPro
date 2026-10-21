"""OCR local : extraction de texte depuis images et PDF, sans connexion Internet."""
import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules import ocr_engine
from modules.paths import client_dir
from . import common as c


class OcrView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.path, self.q, self.clients = "", queue.Queue(), {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        c.title(self, "Lecture de documents (OCR)").grid(row=0, column=0, sticky="w")
        top = c.card(self)
        top.grid(row=1, column=0, sticky="ew", pady=12)
        top.grid_columnconfigure(1, weight=1)
        c.primary_btn(top, "Choisir un fichier", self.pick, width=180).grid(row=0, column=0, padx=14, pady=14)
        self.file_lbl = c.subtitle(top, "Image (PNG, JPG) ou PDF, scanné ou non")
        self.file_lbl.grid(row=0, column=1, sticky="w")
        self.run_btn = c.primary_btn(top, "Extraire le texte", self.run, width=170)
        self.run_btn.grid(row=0, column=2, padx=14)
        self.progress = ctk.CTkProgressBar(top, mode="indeterminate", progress_color=c.ACCENT)
        self.text = ctk.CTkTextbox(self, font=(c.FONT, 13), border_width=1, border_color=c.BORDER, corner_radius=12)
        self.text.grid(row=2, column=0, sticky="nsew")
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", pady=12)
        c.ghost_btn(bar, "Copier le texte", self.copy, width=150).pack(side="left")
        c.ghost_btn(bar, "Enregistrer (.txt)", self.save_as, width=160).pack(side="left", padx=8)
        self.client_cb = ctk.CTkComboBox(bar, values=[""], width=220, height=38)
        self.client_cb.pack(side="right")
        c.ghost_btn(bar, "Archiver chez :", self.archive, width=130).pack(side="right", padx=8)
        self.refresh()

    def refresh(self):
        self.clients = {cl["name"]: cl for cl in self.db.list_clients()}
        names = list(self.clients) or [""]
        self.client_cb.configure(values=names)
        if self.client_cb.get() not in self.clients:
            self.client_cb.set(names[0])

    def pick(self):
        f = filedialog.askopenfilename(filetypes=[("Images et PDF", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.pdf")])
        if f:
            self.path = f
            self.file_lbl.configure(text=Path(f).name, text_color=c.TEXT)

    def run(self):
        if not self.path:
            return c.error("Choisissez d'abord un fichier.")
        self.run_btn.configure(state="disabled", text="Analyse en cours...")
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 12))
        self.progress.start()

        def work():
            try:
                self.q.put(("ok", ocr_engine.extract_text(self.path)))
            except ValueError as e:
                self.q.put(("err", str(e)))
            except Exception:
                self.q.put(("err", "La lecture a échoué. Le fichier est peut-être endommagé."))

        threading.Thread(target=work, daemon=True).start()
        self.after(200, self.poll)

    def poll(self):
        try:
            kind, payload = self.q.get_nowait()
        except queue.Empty:
            return self.after(200, self.poll)
        self.progress.stop()
        self.progress.grid_forget()
        self.run_btn.configure(state="normal", text="Extraire le texte")
        if kind == "err":
            return c.error(payload)
        self.text.delete("1.0", "end")
        self.text.insert("1.0", payload or "(Aucun texte détecté)")

    def _content(self):
        return self.text.get("1.0", "end").strip()

    def copy(self):
        c.copy_to_clipboard(self, self._content())

    def save_as(self):
        f = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texte", "*.txt")])
        if f:
            Path(f).write_text(self._content(), encoding="utf-8")

    def archive(self):
        cl = self.clients.get(self.client_cb.get())
        if not cl or not self._content():
            return c.error("Extrayez du texte et choisissez un entrepreneur.")
        dest = client_dir(cl["name"], "Documents_OCR") / f"{datetime.now():%Y-%m-%d_%H%M%S}_{Path(self.path).stem[:30]}.txt".replace(" ", "_")
        dest.write_text(self._content(), encoding="utf-8")
        c.info(f"Texte archivé dans le dossier de {cl['name']}.")
