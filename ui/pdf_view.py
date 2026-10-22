"""Outils PDF : éditeur visuel, organisation, conversion, sécurité."""
import io
from pathlib import Path
from tkinter import Canvas, Scrollbar, filedialog

import customtkinter as ctk
from PIL import Image, ImageTk

from modules import ocr_layout, pdf_tools
from modules.pdf_tools import PdfEditor
from . import common as c

PDF_TYPES = [("PDF", "*.pdf")]
IMG_TYPES = [("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp")]


class PdfView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.src, self.merge_files, self.src_labels = {}, [], {}
        self.ed, self.page, self.zoom, self.photo = None, 0, 1.2, None
        self.start = None
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x")
        c.title(head, "Outils PDF").pack(side="left")
        self.out = c.OutputPicker(head, self.db)
        self.out.pack(side="right")
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color=c.ACCENT,
                                   segmented_button_selected_hover_color=c.ACCENT_HOVER, fg_color=c.CARD)
        self.tabs.pack(fill="both", expand=True, pady=(8, 0))
        for name in ("Éditeur", "Organiser", "Convertir", "Sécuriser"):
            self.tabs.add(name)
        self._build_editor(self.tabs.tab("Éditeur"))
        self._build_organize(self.tabs.tab("Organiser"))
        self._build_convert(self.tabs.tab("Convertir"))
        self._build_secure(self.tabs.tab("Sécuriser"))

    def refresh(self):
        self.out.refresh()

    # ------------------------------------------------------------ utilitaires
    def _file_row(self, parent, key, text="Choisir un PDF"):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(6, 8))
        lbl = c.subtitle(row, "Aucun fichier")
        c.primary_btn(row, text, lambda: self._pick(key), width=170).pack(side="left")
        lbl.pack(side="left", padx=12)
        self.src_labels[key] = lbl

    def _pick(self, key):
        f = filedialog.askopenfilename(filetypes=PDF_TYPES)
        if f:
            self.src[key] = f
            self.src_labels[key].configure(text=Path(f).name, text_color=c.TEXT)

    def _section(self, parent, text):
        c.label(parent, text, bold=True, size=14).pack(anchor="w", pady=(12, 2))

    def _job(self, key, suffix, fn, sub="Documents_PDF", ext=".pdf"):
        src = self.src.get(key)
        if not src:
            return c.error("Choisissez d'abord un fichier PDF.")
        out = self.out.target(f"{Path(src).stem}{suffix}{ext}", sub)
        if out:
            c.run_bg(self, lambda: fn(src, out), lambda ok, val: self._done(ok, val, out))

    def _done(self, ok, val, out):
        if not ok:
            return c.user_error(val)
        if c.confirm("Terminé ✔\nOuvrir le résultat ?", "PDF"):
            c.open_path(out)

    # ---------------------------------------------------------------- éditeur
    def _build_editor(self, tab):
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x")
        c.primary_btn(bar, "Ouvrir un PDF", self.ed_open, width=140).pack(side="left")
        c.ghost_btn(bar, "◀", lambda: self.ed_goto(-1), width=40).pack(side="left", padx=(10, 2))
        self.page_lbl = c.label(bar, "—", bold=True, width=90)
        self.page_lbl.pack(side="left")
        c.ghost_btn(bar, "▶", lambda: self.ed_goto(1), width=40).pack(side="left", padx=2)
        c.ghost_btn(bar, "−", lambda: self.ed_zoom(0.85), width=40).pack(side="left", padx=(10, 2))
        c.ghost_btn(bar, "+", lambda: self.ed_zoom(1.18), width=40).pack(side="left", padx=2)
        c.primary_btn(bar, "Enregistrer", self.ed_save, width=120).pack(side="right")
        c.ghost_btn(bar, "Supprimer la page", self.ed_delete, width=150, danger=True).pack(side="right", padx=6)
        c.ghost_btn(bar, "Pivoter", self.ed_rotate, width=90).pack(side="right")
        c.ghost_btn(bar, "Annuler", self.ed_undo, width=90).pack(side="right", padx=6)
        tools = ctk.CTkFrame(tab, fg_color="transparent")
        tools.pack(fill="x", pady=8)
        self.tool = ctk.CTkSegmentedButton(tools, values=["Texte", "Image / cachet", "Masquer", "Remplacer", "Surligner"],
                                           selected_color=c.ACCENT, selected_hover_color=c.ACCENT_HOVER)
        self.tool.set("Texte")
        self.tool.pack(side="left")
        self.txt = c.entry(tools, "Texte à ajouter", 220)
        self.txt.pack(side="left", padx=8)
        self.size = c.entry(tools, "12", 52)
        self.size.insert(0, "12")
        self.size.pack(side="left")
        self.color = ctk.CTkComboBox(tools, values=list(pdf_tools.COLORS), width=100, height=38, state="readonly")
        self.color.set("Noir")
        self.color.pack(side="left", padx=6)
        self.img_path = ""
        self.img_btn = c.ghost_btn(tools, "Choisir l'image...", self.ed_pick_image, width=150)
        self.img_btn.pack(side="left")
        c.subtitle(tab, "Texte : cliquez sur la page.  Image, Masquer, Remplacer, Surligner : tracez un rectangle à la souris.").pack(anchor="w")
        holder = ctk.CTkFrame(tab, fg_color=("#D5DAE3", "#0C0F14"), corner_radius=8)
        holder.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas = Canvas(holder, bg="#C9CED8", highlightthickness=0)
        sb = Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-int(e.delta / 120), "units"))

    def ed_open(self):
        f = filedialog.askopenfilename(filetypes=PDF_TYPES)
        if not f:
            return
        pwd = None
        try:
            try:
                self.ed = PdfEditor(f)
            except ValueError:
                pwd = ctk.CTkInputDialog(text="Mot de passe du PDF :", title="PDF protégé").get_input()
                self.ed = PdfEditor(f, pwd)
        except Exception as e:  # noqa: BLE001
            return c.user_error(e, "Impossible d'ouvrir ce PDF.")
        self.ed_name, self.page = Path(f).stem, 0
        self.ed_render()

    def ed_render(self):
        if not self.ed:
            return
        self.page = max(0, min(self.page, self.ed.n - 1))
        img = Image.open(io.BytesIO(self.ed.render(self.page, self.zoom)))
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.configure(scrollregion=(0, 0, img.width, img.height))
        self.page_lbl.configure(text=f"{self.page + 1} / {self.ed.n}")

    def ed_goto(self, d):
        if self.ed:
            self.page += d
            self.ed_render()

    def ed_zoom(self, f):
        self.zoom = max(0.4, min(3.0, self.zoom * f))
        self.ed_render()

    def ed_undo(self):
        if self.ed and self.ed.undo():
            self.ed_render()

    def ed_rotate(self):
        if self.ed:
            self.ed.rotate(self.page, 90)
            self.ed_render()

    def ed_delete(self):
        if self.ed and c.confirm("Supprimer cette page du document ?"):
            try:
                self.ed.delete_page(self.page)
            except ValueError as e:
                return c.error(str(e))
            self.ed_render()

    def ed_pick_image(self):
        f = filedialog.askopenfilename(filetypes=IMG_TYPES)
        if f:
            self.img_path = f
            self.img_btn.configure(text=Path(f).name[:18])

    def ed_save(self):
        if not self.ed:
            return c.error("Ouvrez d'abord un PDF.")
        out = self.out.target(f"{self.ed_name}_modifie.pdf", "Documents_PDF")
        if out:
            try:
                self.ed.save(out)
            except Exception as e:  # noqa: BLE001
                return c.user_error(e)
            if c.confirm("PDF enregistré.\nL'ouvrir maintenant ?", "Terminé"):
                c.open_path(out)

    # souris
    def _press(self, e):
        self.start = (self.canvas.canvasx(e.x), self.canvas.canvasy(e.y))

    def _drag(self, e):
        if self.start:
            self.canvas.delete("sel")
            self.canvas.create_rectangle(*self.start, self.canvas.canvasx(e.x), self.canvas.canvasy(e.y),
                                         outline="#1F5FBF", width=2, dash=(4, 3), tags="sel")

    def _release(self, e):
        if not (self.ed and self.start):
            return
        x0, y0 = self.start
        x1, y1 = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        self.start = None
        self.canvas.delete("sel")
        z = self.zoom
        rect = (min(x0, x1) / z, min(y0, y1) / z, max(x0, x1) / z, max(y0, y1) / z)
        small = (rect[2] - rect[0]) < 6 or (rect[3] - rect[1]) < 6
        tool, pg = self.tool.get(), self.page
        try:
            if tool == "Texte":
                size = float(self.size.get().replace(",", ".") or 12)
                self.ed.add_text(pg, rect[0], rect[1] + size * 0.9, self.txt.get(), size, self.color.get())
            elif tool == "Image / cachet":
                if not self.img_path:
                    return c.error("Choisissez d'abord l'image (signature, cachet, logo).")
                if small:
                    rect = (rect[0], rect[1], rect[0] + 140, rect[1] + 70)
                self.ed.add_image(pg, rect, self.img_path)
            elif small:
                return c.info("Tracez un rectangle avec la souris pour cet outil.")
            elif tool == "Masquer":
                self.ed.redact(pg, rect)
            elif tool == "Surligner":
                self.ed.highlight(pg, rect)
            elif tool == "Remplacer":
                new = ctk.CTkInputDialog(text="Nouveau texte pour cette zone :", title="Remplacer le texte").get_input()
                if new:
                    self.ed.replace_text(pg, rect, new, color=self.color.get())
        except (ValueError, OSError) as ex:
            return c.error(str(ex))
        self.ed_render()

    # -------------------------------------------------------------- organiser
    def _build_organize(self, tab):
        body = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._section(body, "Fusionner plusieurs PDF")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        c.primary_btn(row, "Ajouter des PDF...", self.merge_add, width=170).pack(side="left")
        c.ghost_btn(row, "Vider", self.merge_clear, width=80).pack(side="left", padx=6)
        c.primary_btn(row, "Fusionner", self.merge_run, width=130).pack(side="left")
        self.merge_lbl = c.subtitle(body, "Aucun fichier (l'ordre d'ajout = l'ordre dans le PDF final)", wraplength=700)
        self.merge_lbl.pack(anchor="w", pady=4)
        self._section(body, "Pages d'un PDF")
        self._file_row(body, "org")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        c.label(row, "Pages :", bold=True).pack(side="left")
        self.pages_entry = c.entry(row, "ex. 1-3,5,8-", 200)
        self.pages_entry.pack(side="left", padx=8)
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x", pady=8)
        for t, fn in (("Extraire / réorganiser", self.pg_extract), ("Supprimer ces pages", self.pg_delete),
                      ("Pivoter ↻ 90°", lambda: self.pg_rotate(90)), ("Pivoter ↺ 90°", lambda: self.pg_rotate(270)),
                      ("Séparer en pages", self.pg_split)):
            c.ghost_btn(grid, t, fn, width=170).pack(side="left", padx=(0, 6), pady=2)
        c.subtitle(body, "Réorganiser : saisissez toutes les pages dans le nouvel ordre (ex. 3,1,2).  "
                         "Pivoter : laissez « Pages » vide pour tout le document.", wraplength=700).pack(anchor="w")

    def merge_add(self):
        fs = filedialog.askopenfilenames(filetypes=PDF_TYPES)
        self.merge_files += list(fs)
        self.merge_lbl.configure(text="\n".join(f"{i}. {Path(f).name}" for i, f in enumerate(self.merge_files, 1)) or "Aucun fichier")

    def merge_clear(self):
        self.merge_files = []
        self.merge_lbl.configure(text="Aucun fichier")

    def merge_run(self):
        if len(self.merge_files) < 2:
            return c.error("Ajoutez au moins deux PDF à fusionner.")
        out = self.out.target("fusion.pdf", "Documents_PDF")
        if out:
            files = list(self.merge_files)
            c.run_bg(self, lambda: pdf_tools.merge(files, out), lambda ok, v: self._done(ok, v, out))

    def pg_extract(self):
        self._job("org", "_extrait", lambda s, o: pdf_tools.extract_pages(s, self.pages_entry.get(), o))

    def pg_delete(self):
        self._job("org", "_sans_pages", lambda s, o: pdf_tools.delete_pages(s, self.pages_entry.get(), o))

    def pg_rotate(self, angle):
        self._job("org", "_pivote", lambda s, o: pdf_tools.rotate_pages(s, self.pages_entry.get(), angle, o))

    def pg_split(self):
        src = self.src.get("org")
        if not src:
            return c.error("Choisissez d'abord un fichier PDF.")
        folder = self.out.folder("Documents_PDF")
        if folder:
            c.run_bg(self, lambda: pdf_tools.split_each(src, folder, Path(src).stem),
                     lambda ok, v: c.user_error(v) if not ok else (c.info(f"{len(v)} fichiers créés."), c.open_path(folder)))

    # --------------------------------------------------------------- convertir
    def _build_convert(self, tab):
        body = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._section(body, "PDF → Word (mise en page, tableaux et images conservés)")
        self._file_row(body, "conv")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        c.primary_btn(row, "Convertir en Word", self.to_word, width=180).pack(side="left")
        c.ghost_btn(row, "Convertir en images (PNG)", self.to_images, width=220).pack(side="left", padx=8)
        c.subtitle(body, "Les PDF scannés sont lus automatiquement par OCR.").pack(anchor="w", pady=4)
        self._section(body, "Images → PDF")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        c.primary_btn(row, "Choisir des images et créer le PDF", self.imgs_to_pdf, width=300).pack(side="left")

    def to_word(self):
        self._job("conv", "", lambda s, o: ocr_layout.export_docx(ocr_layout.analyze(s), o), "Documents_OCR", ".docx")

    def to_images(self):
        src = self.src.get("conv")
        if not src:
            return c.error("Choisissez d'abord un fichier PDF.")
        folder = self.out.folder("Documents_PDF")
        if folder:
            c.run_bg(self, lambda: pdf_tools.pdf_to_images(src, folder, Path(src).stem),
                     lambda ok, v: c.user_error(v) if not ok else (c.info(f"{len(v)} image(s) créée(s)."), c.open_path(folder)))

    def imgs_to_pdf(self):
        fs = filedialog.askopenfilenames(filetypes=IMG_TYPES)
        if not fs:
            return
        out = self.out.target("images.pdf", "Documents_PDF")
        if out:
            c.run_bg(self, lambda: pdf_tools.images_to_pdf(list(fs), out), lambda ok, v: self._done(ok, v, out))

    # --------------------------------------------------------------- sécuriser
    def _build_secure(self, tab):
        body = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        body.pack(fill="both", expand=True)
        self._file_row(body, "sec")
        self._section(body, "Mot de passe")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self.pwd = c.entry(row, "Mot de passe", 220, show="•")
        self.pwd.pack(side="left")
        c.primary_btn(row, "Protéger", self.do_protect, width=120).pack(side="left", padx=8)
        c.ghost_btn(row, "Retirer la protection", self.do_unprotect, width=180).pack(side="left")
        self._section(body, "Filigrane")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        self.wm = c.entry(row, "ex. CONFIDENTIEL, COPIE, BROUILLON", 300)
        self.wm.pack(side="left")
        c.primary_btn(row, "Ajouter le filigrane", self.do_wm, width=180).pack(side="left", padx=8)
        self._section(body, "Autres")
        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")
        c.ghost_btn(row, "Numéroter les pages", self.do_numbers, width=190).pack(side="left")
        c.ghost_btn(row, "Réduire la taille", self.do_compress, width=170).pack(side="left", padx=8)

    def do_protect(self):
        self._job("sec", "_protege", lambda s, o: pdf_tools.protect(s, o, self.pwd.get()))

    def do_unprotect(self):
        self._job("sec", "_deverrouille", lambda s, o: pdf_tools.unprotect(s, o, self.pwd.get()))

    def do_wm(self):
        self._job("sec", "_filigrane", lambda s, o: pdf_tools.watermark(s, o, self.wm.get()))

    def do_numbers(self):
        self._job("sec", "_numerote", lambda s, o: pdf_tools.number_pages(s, o))

    def do_compress(self):
        self._job("sec", "_reduit", lambda s, o: pdf_tools.compress(s, o))
