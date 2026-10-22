"""Rédaction : documents types, mise en forme automatique, montant en lettres."""
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules import writer
from modules.numwords import amount_in_words
from modules.paths import safe_name
from . import common as c


class WriterView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.fields, self.els = {}, []
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x")
        c.title(head, "Rédaction").pack(side="left")
        self.out = c.OutputPicker(head, self.db)
        self.out.pack(side="right")
        self.lang_seg = c.lang_selector(head, 130)
        self.lang_seg.pack(side="right", padx=(0, 14))
        c.label(head, "Langue du document", bold=True, size=12, color=c.MUTED).pack(side="right", padx=(0, 6))
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color=c.ACCENT,
                                   segmented_button_selected_hover_color=c.ACCENT_HOVER, fg_color=c.CARD)
        self.tabs.pack(fill="both", expand=True, pady=(8, 0))
        for name in ("Documents types", "Mise en forme automatique", "Montant en lettres"):
            self.tabs.add(name)
        self._build_types(self.tabs.tab("Documents types"))
        self._build_format(self.tabs.tab("Mise en forme automatique"))
        self._build_amount(self.tabs.tab("Montant en lettres"))

    def refresh(self):
        self.out.refresh()
        names = ["Sans en-tête"] + [cl["name"] for cl in self.db.list_clients()]
        self.sender_cb.configure(values=names)
        if self.sender_cb.get() not in names:
            self.sender_cb.set(names[0])

    # --------------------------------------------------------- documents types
    def _build_types(self, tab):
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x")
        self.type_cb = ctk.CTkComboBox(top, values=list(writer.DOC_TYPES), width=240, height=38, state="readonly",
                                       command=lambda _: self.build_form())
        self.type_cb.set("Lettre administrative")
        self.type_cb.pack(side="left")
        self.sender_cb = ctk.CTkComboBox(top, values=["Sans en-tête"], width=220, height=38, state="readonly")
        self.sender_cb.set("Sans en-tête")
        self.sender_cb.pack(side="left", padx=8)
        self.style_cb = ctk.CTkComboBox(top, values=list(writer.STYLES), width=210, height=38, state="readonly")
        self.style_cb.set("Classique (Times 12)")
        self.style_cb.pack(side="left")
        self.form = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.form.pack(fill="both", expand=True, pady=8)
        self.form.grid_columnconfigure((0, 1), weight=1, uniform="f")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x")
        c.primary_btn(bar, "Générer en Word", lambda: self.generate("docx"), width=170).pack(side="left")
        c.primary_btn(bar, "Générer en PDF", lambda: self.generate("pdf"), width=170).pack(side="left", padx=8)
        self.build_form()

    def build_form(self):
        for w in self.form.winfo_children():
            w.destroy()
        self.fields = {}
        _, spec = writer.DOC_TYPES[self.type_cb.get()]
        r = col = 0
        for key, text, kind in spec:
            wide = kind == "text"
            if wide and col == 1:
                r, col = r + 1, 0
            box = ctk.CTkFrame(self.form, fg_color="transparent")
            box.grid(row=r, column=col, columnspan=2 if wide else 1, sticky="ew", padx=8, pady=5)
            c.label(box, text, bold=True, size=12, color=c.MUTED).pack(anchor="w", pady=(0, 3))
            if wide:
                w = ctk.CTkTextbox(box, height=96, border_width=1, border_color=c.BORDER, corner_radius=8)
            else:
                w = c.entry(box, "", 200)
            w.pack(fill="x")
            self.fields[key] = w
            if wide:
                r, col = r + 1, 0
            else:
                col = 1 - col
                r += col == 0

    def _value(self, w):
        return w.get("1.0", "end").strip() if isinstance(w, ctk.CTkTextbox) else w.get().strip()

    def _sender(self):
        name = self.sender_cb.get()
        return next((cl for cl in self.db.list_clients() if cl["name"] == name), None)

    def generate(self, kind):
        dtype = self.type_cb.get()
        try:
            els = writer.build_document(dtype, {k: self._value(w) for k, w in self.fields.items()}, self._sender(),
                                        c.lang_code(self.lang_seg))
        except ValueError as e:
            return c.error(str(e))
        self._export(els, f"{safe_name(dtype)}_{date.today().isoformat()}", kind)

    def _export(self, els, stem, kind):
        out = self.out.target(f"{stem}.{kind}", "Documents_Generes")
        if not out:
            return
        style = self.style_cb.get()
        fn = writer.to_docx if kind == "docx" else writer.to_pdf

        def done(ok, val):
            if not ok:
                return c.user_error(val)
            if c.confirm("Document créé.\nL'ouvrir maintenant ?", "Terminé"):
                c.open_path(out)

        c.run_bg(self, lambda: fn(els, out, style), done)

    # ------------------------------------------------------- mise en forme auto
    def _build_format(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1, uniform="c")
        tab.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        c.ghost_btn(top, "Ouvrir un fichier (txt, docx, pdf)", self.open_source, width=260).pack(side="left")
        c.primary_btn(top, "Mettre en forme automatiquement  ➜", self.auto_format, width=300).pack(side="left", padx=8)
        self.src_box = ctk.CTkTextbox(tab, font=(c.FONT, 13), border_width=1, border_color=c.BORDER, corner_radius=10)
        self.src_box.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.dst_box = ctk.CTkTextbox(tab, font=(c.FONT, 13), border_width=1, border_color=c.BORDER, corner_radius=10)
        self.dst_box.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        c.subtitle(tab, "Collez ou ouvrez votre texte (même brut, issu d'un scan) : titres, listes, paragraphes, "
                        "majuscules et ponctuation française sont corrigés.", wraplength=780).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=4)
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.grid(row=3, column=0, columnspan=2, sticky="ew")
        c.primary_btn(bar, "Word", lambda: self.export_formatted("docx"), width=110).pack(side="left")
        c.primary_btn(bar, "PDF", lambda: self.export_formatted("pdf"), width=110).pack(side="left", padx=6)
        c.ghost_btn(bar, "Copier le résultat", lambda: c.copy_to_clipboard(self, self.dst_box.get("1.0", "end").strip()),
                    width=170).pack(side="left")

    def load_text(self, text):
        self.tabs.set("Mise en forme automatique")
        self.src_box.delete("1.0", "end")
        self.src_box.insert("1.0", text)

    def open_source(self):
        f = filedialog.askopenfilename(filetypes=[("Documents", "*.txt *.docx *.pdf")])
        if not f:
            return
        try:
            ext = Path(f).suffix.lower()
            if ext == ".txt":
                text = Path(f).read_text(encoding="utf-8", errors="replace")
            elif ext == ".docx":
                from docx import Document
                text = "\n\n".join(p.text for p in Document(f).paragraphs)
            else:
                import pymupdf
                with pymupdf.open(f) as d:
                    text = "\n\n".join(p.get_text() for p in d)
                if len(text.strip()) < 30:
                    return c.info("Ce PDF est une image : utilisez d'abord « Numérisation (OCR) », "
                                  "puis « Envoyer vers Rédaction ».")
        except Exception as e:  # noqa: BLE001
            return c.user_error(e, "Ce fichier n'a pas pu être lu.")
        self.load_text(text)

    def auto_format(self):
        raw = self.src_box.get("1.0", "end").strip()
        if not raw:
            return c.error("Collez ou ouvrez d'abord un texte.")
        self.els = writer.format_text(raw, lang=c.lang_code(self.lang_seg))
        self.dst_box.delete("1.0", "end")
        self.dst_box.insert("1.0", writer.elements_to_text(self.els))

    def export_formatted(self, kind):
        if not self.els:
            self.auto_format()
        if self.els:
            self._export(self.els, f"texte_mis_en_forme_{date.today().isoformat()}", kind)

    # ----------------------------------------------------------------- montant
    def _build_amount(self, tab):
        c.subtitle(tab, "Écrivez un montant en toutes lettres (chèques, reçus, factures, contrats).").pack(anchor="w", pady=(6, 8))
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x")
        self.amount = c.entry(row, "Montant, ex. 1857250", 220)
        self.amount.pack(side="left")
        self.cur = c.entry(row, "FCFA", 90)
        self.cur.insert(0, "FCFA")
        self.cur.pack(side="left", padx=8)
        c.primary_btn(row, "Écrire en lettres", self.words, width=170).pack(side="left")
        self.words_lbl = c.label(tab, "", size=16, bold=True, wraplength=760, justify="left")
        self.words_lbl.pack(anchor="w", pady=16)
        c.ghost_btn(tab, "Copier", lambda: c.copy_to_clipboard(self, self.words_lbl.cget("text")), width=100).pack(anchor="w")

    def words(self):
        try:
            v = Decimal(self.amount.get().replace(" ", "").replace(",", "."))
            self.words_lbl.configure(text=amount_in_words(v, self.cur.get().strip().upper() or "FCFA", c.lang_code(self.lang_seg)) + ".",
                                     text_color=c.TEXT)
        except (InvalidOperation, ValueError):
            self.words_lbl.configure(text="Montant invalide (chiffres uniquement, jusqu'à 999 milliards).", text_color=c.DANGER)
