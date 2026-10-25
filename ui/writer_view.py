"""Rédaction : documents types, mise en forme automatique, montant en lettres."""
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules import ai_local, ai_manager, writer
from modules.ai_cloud import AIUnavailable
from modules.numwords import amount_in_words
from modules.paths import safe_name
from . import common as c


class WriterView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.fields, self.els = {}, []
        self.ai_running = False
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
        for name in ("Documents types", "Assistant IA", "Mise en forme automatique", "Montant en lettres"):
            self.tabs.add(name)
        self._build_types(self.tabs.tab("Documents types"))
        self._build_ai(self.tabs.tab("Assistant IA"))
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
        c.ghost_btn(bar, "✨  Rédiger avec l'IA", self.ai_fill_field, width=210).pack(side="left")
        self.ai_note = c.label(bar, "", color=c.ACCENT, size=12)
        self.ai_note.pack(side="left", padx=10)
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

    # ------------------------------------------------------------ IA locale
    def _ai_run(self, messages, sink, finish, fallback=None, max_tokens=700):
        """Essaie l'IA (locale / en ligne, selon la configuration de l'administrateur) puis, sinon, le repli de l'application."""
        if self.ai_running:
            return c.info("Une rédaction est déjà en cours. Patientez un instant.")
        snap = ai_manager.snapshot(self.db)
        if not ai_manager.enabled(snap):
            return c.error("L'IA n'est pas activée. L'administrateur peut l'activer dans le menu « Intelligence artificielle ».", "IA")
        self.ai_running = True
        self.ai_note.configure(text="Rédaction en cours... (le premier lancement du modèle peut prendre 1 minute)")
        buf, used = [], [""]

        def on_tok(t):
            if t is None:                     # un fournisseur a échoué en cours de route : on repart de zéro
                buf.clear()
            else:
                buf.append(t)
            sink(t)

        def producer(cb):
            used[0] = ai_manager.run(snap, messages, cb, max_tokens=max_tokens)[1]

        def done(ok2, err):
            self.ai_running = False
            ai_manager.persist_cooldowns(self.db)
            if ok2:
                self.ai_note.configure(text=c.tr("✔ rédigé par : {x}", x=used[0]))
                return finish(ai_local.clean_output("".join(buf)))
            self.ai_note.configure(text="")
            if isinstance(err, AIUnavailable):
                if fallback is None:
                    return c.error(c.tr("L'IA est indisponible pour le moment : {x}", x=ai_manager.short_reasons(err)), "IA")
                finish(fallback())
                self.ai_note.configure(text="Mise en forme automatique de l'application appliquée.")
                return c.info(c.tr("L'IA est indisponible pour le moment ({x}). L'application a utilisé sa propre mise en forme automatique.",
                                   x=ai_manager.short_reasons(err)), "IA")
            c.user_error(err, "La génération a échoué. Le modèle est peut-être trop lourd pour cet ordinateur.")

        c.stream_bg(self, producer, on_tok, done)

    @staticmethod
    def _put(widget, text, clear=False):
        if isinstance(widget, ctk.CTkTextbox):
            if clear:
                widget.delete("1.0", "end")
            widget.insert("end", text)
        else:
            if clear:
                widget.delete(0, "end")
            widget.insert("end", text.replace("\n", " "))

    def ai_fill_field(self):
        dtype = self.type_cb.get()
        if dtype not in ai_local.AI_FIELDS:
            return c.info("Pas de rédaction IA pour ce type de document : utilisez l'onglet « Assistant IA ».")
        values = {k: self._value(w) for k, w in self.fields.items()}
        key, messages = ai_local.messages_for_doc(dtype, values, c.lang_code(self.lang_seg))
        target = self.fields[key]
        first = [True]

        def sink(tok):
            if tok is None:
                first[0] = True
                return
            self._put(target, tok, clear=first[0])
            first[0] = False

        lang = c.lang_code(self.lang_seg)

        def fallback():
            notes = values.get(key, "").strip()
            if notes:
                return writer.elements_to_text(writer.format_text(notes, lang=lang))
            return writer.FALLBACK_TEXT.get(lang, writer.FALLBACK_TEXT["fr"]).get(key, "").format(objet=values.get("objet", "…"))

        self._ai_run(messages, sink, lambda text: self._put(target, text, clear=True), fallback)

    def _build_ai(self, tab):
        c.subtitle(tab, "Décrivez le texte voulu : l'IA locale le rédige sur cet ordinateur, sans Internet. "
                        "Ex. : « Lettre au maire pour demander un rendez-vous au sujet du permis de construire de la villa Obiang ».",
                   wraplength=780).pack(anchor="w", pady=(4, 6))
        self.ai_req = ctk.CTkTextbox(tab, height=90, border_width=1, border_color=c.BORDER, corner_radius=8, font=(c.FONT, 13))
        self.ai_req.pack(fill="x")
        bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=8)
        c.primary_btn(bar, "✨  Rédiger", self.ai_free, width=150).pack(side="left")
        c.ghost_btn(bar, "Mettre en forme et exporter  ➜", self.ai_to_format, width=290).pack(side="left", padx=8)
        self.ai_out = ctk.CTkTextbox(tab, border_width=1, border_color=c.BORDER, corner_radius=10, font=(c.FONT, 13))
        self.ai_out.pack(fill="both", expand=True)

    def ai_free(self):
        req = self.ai_req.get("1.0", "end").strip()
        if not req:
            return c.error("Décrivez d'abord le texte à rédiger.")
        first = [True]

        def sink(tok):
            if tok is None:
                first[0] = True
                return
            self._put(self.ai_out, tok, clear=first[0])
            first[0] = False

        lang = c.lang_code(self.lang_seg)
        self._ai_run(ai_local.messages_free(req, lang), sink, lambda text: self._put(self.ai_out, text, clear=True),
                     lambda: writer.elements_to_text(writer.format_text(req, lang=lang)), max_tokens=900)

    def ai_to_format(self):
        text = self.ai_out.get("1.0", "end").strip()
        if not text:
            return c.error("Rédigez d'abord un texte avec l'IA.")
        self.load_text(text)
        self.auto_format()

    def ai_improve(self):
        raw = self.src_box.get("1.0", "end").strip()
        if not raw:
            return c.error("Collez ou ouvrez d'abord un texte.")
        first = [True]

        def sink(tok):
            if tok is None:
                first[0] = True
                return
            self._put(self.dst_box, tok, clear=first[0])
            first[0] = False

        def finish(text):
            self.src_box.delete("1.0", "end")
            self.src_box.insert("1.0", text)
            self.auto_format()

        lang = c.lang_code(self.lang_seg)
        self._ai_run(ai_local.messages_improve(raw, lang), sink, finish,
                     lambda: writer.elements_to_text(writer.format_text(raw, lang=lang)), max_tokens=1200)

    # ------------------------------------------------------- mise en forme auto
    def _build_format(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1, uniform="c")
        tab.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        c.ghost_btn(top, "Ouvrir un fichier (txt, docx, pdf)", self.open_source, width=260).pack(side="left")
        c.ghost_btn(top, "✨  Améliorer avec l'IA", self.ai_improve, width=210).pack(side="left", padx=(8, 0))
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
