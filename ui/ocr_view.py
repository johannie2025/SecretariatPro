"""Numérisation (OCR) : texte + mise en page (tableaux, images) → Word / PDF / texte."""
import io
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from modules import ai_manager, ocr_layout, writer
from modules.ai_cloud import AIUnavailable
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
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        self.summary = c.label(row2, "", color=c.ACCENT, bold=True, size=13)
        self.summary.pack(side="left")
        self.thumbs = ctk.CTkFrame(row2, fg_color="transparent")
        self.thumbs.pack(side="left", padx=14)
        self._thumb_refs = []
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
        self.ai_btn = c.ghost_btn(btns, "Word (texte IA)", self.export_docx_ai, width=170)
        c.ghost_btn(btns, "Enregistrer les images", self.save_images, width=200).pack(side="left", padx=6)
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
        self.show_thumbs(val.figures)
        self.ai_btn.pack_forget()
        snap = ai_manager.snapshot(self.db)
        if val.kind != "pdf_text" and ai_manager.ocr_ready(snap):
            self.start_ai_ocr(val, snap, info)

    # ------------------------------------------------------------- OCR IA
    @staticmethod
    def _shrink(jpg):
        im = Image.open(io.BytesIO(jpg)).convert("RGB")
        im.thumbnail((1800, 1800))
        out = io.BytesIO()
        im.save(out, "JPEG", quality=82)
        return out.getvalue()

    def start_ai_ocr(self, res, snap, info):
        """OCR par modèle à vision (si l'administrateur l'a activé) ; repli : OCR de l'application, page par page."""
        self.summary.configure(text=info + "  •  " + c.tr("OCR IA en cours..."))
        self.run_btn.configure(state="disabled")

        def job():
            texts, labels, failed, last = [], [], 0, None
            for pg in res.pages:
                if failed >= 2 and not labels:                        # l'IA ne répond pas : on n'insiste pas
                    texts.append(ocr_layout._plain_text(pg))
                    failed += 1
                    continue
                try:
                    t, label = ai_manager.ocr_page(snap, self._shrink(pg.jpg))
                    texts.append(t)
                    if label not in labels:
                        labels.append(label)
                except AIUnavailable as e:
                    failed += 1
                    last = e
                    texts.append(ocr_layout._plain_text(pg))
            return texts, labels, failed, last

        def done(ok, val):
            ai_manager.persist_cooldowns(self.db)
            self.run_btn.configure(state="normal")
            if not ok:
                self.summary.configure(text=info)
                return c.user_error(val)
            texts, labels, failed, last = val
            if failed >= len(res.pages):
                self.summary.configure(text=info + "  •  " + c.tr("OCR IA indisponible : OCR de l'application utilisé"))
                return c.info(c.tr("L'OCR IA est indisponible ({x}). L'OCR intégré de l'application a été utilisé.",
                                   x=ai_manager.short_reasons(last) if last else "—"), "OCR")
            res.ai_text = ocr_layout.clean_text("\n\n".join(texts))
            self.text.delete("1.0", "end")
            self.text.insert("1.0", res.ai_text or c.tr("(Aucun texte détecté)"))
            extra = c.tr("OCR IA : {x}", x=", ".join(labels))
            if failed:
                extra += " " + c.tr("({n} page(s) lue(s) par l'OCR de l'application)", n=failed)
            self.summary.configure(text=info + "  •  " + extra)
            self.ai_btn.pack(side="left", padx=6)

        c.run_bg(self, job, done)

    def export_docx_ai(self):
        """Word reconstruit à partir du texte lu par l'IA (titres, listes, tableaux) + images extraites."""
        if not self._ready() or not getattr(self.result, "ai_text", ""):
            return
        out = self.out.target(f"{Path(self.path).stem}_texte_IA.docx", "Documents_OCR")
        if not out:
            return
        text = self.text.get("1.0", "end").strip()
        els = writer.format_text(text, with_typo=False)
        for fig in self.result.figures:
            els.append({"t": "image", "data": fig["data"], "width": 10})

        def done(ok, val):
            if not ok:
                return c.user_error(val)
            if c.confirm("Fichier enregistré.\nL'ouvrir maintenant ?", "Terminé"):
                c.open_path(out)

        c.run_bg(self, lambda: writer.to_docx(els, out, "Moderne (Calibri 11)"), done)

    def show_thumbs(self, figures):
        for w in self.thumbs.winfo_children():
            w.destroy()
        self._thumb_refs = []
        for fig in figures[:8]:
            try:
                im = Image.open(io.BytesIO(fig["data"])).convert("RGB")
                im.thumbnail((90, 56))
                ci = ctk.CTkImage(light_image=im, dark_image=im, size=im.size)
            except Exception:
                continue
            self._thumb_refs.append(ci)
            ctk.CTkLabel(self.thumbs, image=ci, text="").pack(side="left", padx=3)

    def save_images(self):
        if not self._ready():
            return
        if not self.result.figures:
            return c.info("Aucune image détectée dans ce document.")
        folder = self.out.folder("Images_OCR")
        if not folder:
            return
        stem = Path(self.path).stem
        for fig in self.result.figures:
            c.unique_path(folder / f"{stem}_{fig['name']}").write_bytes(fig["data"])
        c.info(c.tr("{n} image(s) enregistrée(s).", n=len(self.result.figures)))
        c.open_path(folder)

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
