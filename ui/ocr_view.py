"""Numérisation (OCR) : texte + mise en page (tableaux, images) → Word / PDF / texte."""
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules import ocr_layout
from . import common as c


class OcrView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.path, self.result = "", None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        c.title(self, "Numérisation (OCR)").grid(row=0, column=0, sticky="w")
        top = c.card(self)
        top.grid(row=1, column=0, sticky="ew", pady=(10, 6))
        top.grid_columnconfigure(1, weight=1)
        c.primary_btn(top, "Choisir un fichier", self.pick, width=180).grid(row=0, column=0, padx=14, pady=14)
        self.file_lbl = c.subtitle(top, "Photo, scan ou PDF — texte, tableaux et images sont conservés")
        self.file_lbl.grid(row=0, column=1, sticky="w")
        self.run_btn = c.primary_btn(top, "Analyser le document", self.run, width=200)
        self.run_btn.grid(row=0, column=2, padx=14)
        self.progress = ctk.CTkProgressBar(top, mode="indeterminate", progress_color=c.ACCENT)
        self.summary = c.label(self, "", color=c.ACCENT, bold=True, size=13)
        self.summary.grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.text = ctk.CTkTextbox(self, font=(c.FONT, 13), border_width=1, border_color=c.BORDER, corner_radius=12)
        self.text.grid(row=3, column=0, sticky="nsew")
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.out = c.OutputPicker(bar, self.db)
        self.out.pack(side="left")
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=5, column=0, sticky="ew", pady=8)
        c.primary_btn(btns, "Word (.docx)", self.export_docx, width=140).pack(side="left")
        c.primary_btn(btns, "PDF recherchable", self.export_pdf, width=160).pack(side="left", padx=6)
        c.ghost_btn(btns, "Texte (.txt)", self.export_txt, width=120).pack(side="left")
        c.ghost_btn(btns, "Copier", self.copy, width=90).pack(side="left", padx=6)
        c.ghost_btn(btns, "Envoyer vers Rédaction", self.to_writer, width=190).pack(side="right")

    def refresh(self):
        self.out.refresh()

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
        c.run_bg(self, lambda: ocr_layout.analyze(self.path), self.finished)

    def finished(self, ok, val):
        self.progress.stop()
        self.progress.grid_forget()
        self.run_btn.configure(state="normal", text="Analyser le document")
        if not ok:
            return c.user_error(val, "La lecture a échoué. Le fichier est peut-être endommagé.")
        self.result = val
        self.text.delete("1.0", "end")
        self.text.insert("1.0", val.text or "(Aucun texte détecté)")
        info = "  •  ".join([c.tr("{n} page(s)", n=val.n_pages), c.tr("{n} tableau(x)", n=val.n_tables),
                              c.tr("{n} image(s)/dessin(s)", n=val.n_figures)])
        if val.kind == "pdf_text":
            info += "  •  " + c.tr("PDF numérique : mise en page d'origine reprise")
        self.summary.configure(text=info)

    def _ready(self):
        if not self.result:
            c.error("Analysez d'abord un document.")
            return False
        return True

    def _export(self, suffix, ext, fn):
        if not self._ready():
            return
        out = self.out.target(f"{Path(self.path).stem}{suffix}{ext}", "Documents_OCR")
        if not out:
            return

        def done(ok, val):
            if not ok:
                return c.user_error(val)
            if c.confirm("Fichier enregistré.\nL'ouvrir maintenant ?", "Terminé"):
                c.open_path(out)

        c.run_bg(self, lambda: fn(self.result, out), done)

    def export_docx(self):
        self._export("", ".docx", ocr_layout.export_docx)

    def export_pdf(self):
        self._export("_recherchable", ".pdf", ocr_layout.export_pdf)

    def export_txt(self):
        if not self._ready():
            return
        out = self.out.target(f"{Path(self.path).stem}.txt", "Documents_OCR")
        if out:
            out.write_text(self.text.get("1.0", "end").strip(), encoding="utf-8")
            c.info("Texte enregistré.")

    def copy(self):
        c.copy_to_clipboard(self, self.text.get("1.0", "end").strip())

    def to_writer(self):
        if self._ready():
            self.app.pages["writer"].load_text(self.text.get("1.0", "end").strip())
            self.app.show("writer")
