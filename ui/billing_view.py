"""Facturation : devis, proforma et factures pour les clients des entrepreneurs."""
from decimal import Decimal
from pathlib import Path

import customtkinter as ctk

from modules import billing
from modules.i18n import get_lang
from . import common as c


class BillingView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.rows = []
        self.clients = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        c.title(self, "Facturation").grid(row=0, column=0, sticky="w")
        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        for fr in (self.list_frame, self.form_frame):
            fr.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        self.form_frame.grid_columnconfigure(0, weight=1)
        self.form_frame.grid_rowconfigure(1, weight=1)
        c.ghost_btn(self.form_frame, "←  Retour à la liste", self.show_list, width=200).grid(row=0, column=0, sticky="w", pady=(0, 8))
        body = ctk.CTkScrollableFrame(self.form_frame, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        self._build_list()

        top = c.card(body)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure((0, 1, 2), weight=1, uniform="t")
        self._lbl(top, "Entrepreneur *", 0, 0)
        self.client_cb = ctk.CTkComboBox(top, values=[""], height=38, command=lambda _: self.on_client())
        self.client_cb.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._lbl(top, "Type de document", 0, 1)
        self.type_cb = ctk.CTkSegmentedButton(top, values=list(billing.DOC_TYPES), height=38,
                                              selected_color=c.ACCENT, selected_hover_color=c.ACCENT_HOVER)
        self.type_cb.set("Facture")
        self.type_cb.grid(row=1, column=1, sticky="ew", padx=14, pady=(0, 12))
        self._lbl(top, "Client final *", 0, 2)
        self.final_name = c.entry(top, "Nom du client")
        self.final_name.grid(row=1, column=2, sticky="ew", padx=14, pady=(0, 12))
        self._lbl(top, "Langue du document", 4, 0)
        self.doc_lang = c.lang_selector(top)
        self.doc_lang.grid(row=5, column=0, sticky="w", padx=14, pady=(0, 14))
        self._lbl(top, "Adresse du client final", 2, 0)
        self.final_addr = c.entry(top, "")
        self.final_addr.grid(row=3, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))
        self._lbl(top, "Téléphone", 2, 2)
        self.final_phone = c.entry(top, "")
        self.final_phone.grid(row=3, column=2, sticky="ew", padx=14, pady=(0, 14))

        lines = c.card(body)
        lines.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        lines.grid_columnconfigure(0, weight=1)
        c.label(lines, "Lignes du document", bold=True, size=15).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        self.items_frame = ctk.CTkFrame(lines, fg_color="transparent")
        self.items_frame.grid(row=1, column=0, sticky="ew", padx=10)
        self.items_frame.grid_columnconfigure(0, weight=1)
        hdr = ("Désignation", "Qté", "Prix unitaire", "Montant", "")
        for i, h in enumerate(hdr):
            c.label(self.items_frame, h, bold=True, size=11, color=c.MUTED).grid(row=0, column=i, sticky="w", padx=4)
        c.ghost_btn(lines, "+  Ajouter une ligne", self.add_row, width=170).grid(row=2, column=0, sticky="w", padx=14, pady=12)

        bottom = c.card(body)
        bottom.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(bottom, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=14, pady=12)
        c.label(left, "Remise (%)", bold=True, size=12, color=c.MUTED).grid(row=0, column=0, sticky="w")
        c.label(left, "Taxe / TVA (%)", bold=True, size=12, color=c.MUTED).grid(row=0, column=1, sticky="w", padx=10)
        self.discount = c.entry(left, "0", 110)
        self.discount.insert(0, "0")
        self.discount.grid(row=1, column=0, sticky="w")
        self.tax = c.entry(left, "0", 110)
        self.tax.insert(0, "0")
        self.tax.grid(row=1, column=1, sticky="w", padx=10)
        for e in (self.discount, self.tax):
            e.bind("<KeyRelease>", lambda ev: self.recalc())
        c.label(left, "Notes / conditions de paiement", bold=True, size=12, color=c.MUTED).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.notes = ctk.CTkTextbox(left, height=70, border_width=1, border_color=c.BORDER, corner_radius=8)
        self.notes.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.totals = c.label(bottom, "", size=14, justify="right")
        self.totals.configure(anchor="e")
        self.totals.grid(row=0, column=1, sticky="e", padx=20)
        c.primary_btn(body, "Générer le PDF", self.generate, width=220).grid(row=3, column=0, sticky="e", pady=(0, 14))

        self.refresh()
        self.show_list()

    def _lbl(self, parent, text, r, col):
        c.label(parent, text, bold=True, size=12, color=c.MUTED).grid(row=r, column=col, sticky="w", padx=14, pady=(12, 3))

    # -------------------------------------------------------------- données
    def refresh(self):
        self.clients = {cl["name"]: cl for cl in self.db.list_clients()}
        names = list(self.clients) or [""]
        self.client_cb.configure(values=names)
        if self.client_cb.get() not in self.clients:
            self.client_cb.set(names[0])
        names_f = ["Tous"] + list(self.clients)
        self.f_client.configure(values=names_f)
        if self.f_client.get() not in names_f:
            self.f_client.set("Tous")
        self.on_client()
        if not self.rows:
            self.add_row()
        self.load_history()

    # ------------------------------------------------- liste / formulaire
    def _build_list(self):
        lf = self.list_frame
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(2, weight=1)
        bar = ctk.CTkFrame(lf, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew")
        c.primary_btn(bar, "+  Créer une facture / un devis", self.show_form, width=270).pack(side="right")
        self.f_search = c.entry(bar, "Rechercher (n°, client, entrepreneur, date...)", 340)
        self.f_search.pack(side="left")
        self.f_search.bind("<KeyRelease>", lambda e: self.load_history())
        self.f_type = ctk.CTkComboBox(bar, values=["Tous"] + list(billing.DOC_TYPES), width=130, height=38, state="readonly",
                                      command=lambda _: self.load_history())
        self.f_type.set("Tous")
        self.f_type.pack(side="left", padx=8)
        self.f_client = ctk.CTkComboBox(bar, values=["Tous"], width=190, height=38, state="readonly",
                                        command=lambda _: self.load_history())
        self.f_client.set("Tous")
        self.f_client.pack(side="left")
        self.count_lbl = c.subtitle(lf, "")
        self.count_lbl.grid(row=1, column=0, sticky="w", pady=(8, 2))
        self.history = ctk.CTkScrollableFrame(lf, fg_color="transparent")
        self.history.grid(row=2, column=0, sticky="nsew")

    def show_list(self):
        self.form_frame.grid_remove()
        self.list_frame.grid()
        self.load_history()

    def show_form(self):
        if not self.clients:
            return c.error("Créez d'abord un entrepreneur dans l'onglet « Entrepreneurs ».", "Aucun entrepreneur")
        self.final_name.delete(0, "end")
        self.final_addr.delete(0, "end")
        self.final_phone.delete(0, "end")
        self.notes.delete("1.0", "end")
        while len(self.rows) > 1:
            self.remove_row(self.rows[-1])
        for k in ("desc",):
            self.rows[0][k].delete(0, "end")
        self.rows[0]["price"].delete(0, "end")
        self.rows[0]["price"].insert(0, "0")
        self.discount.delete(0, "end")
        self.discount.insert(0, "0")
        self.on_client()
        self.list_frame.grid_remove()
        self.form_frame.grid()

    def on_client(self):
        cl = self.clients.get(self.client_cb.get())
        if cl:
            self.tax.delete(0, "end")
            self.tax.insert(0, str(cl["tax_rate"]).rstrip("0").rstrip(".") if cl["tax_rate"] else "0")
        self.recalc()

    def add_row(self):
        r = len(self.rows) + 1
        desc = c.entry(self.items_frame, "Ex. : Plan architectural", 300)
        qty = c.entry(self.items_frame, "1", 70)
        qty.insert(0, "1")
        price = c.entry(self.items_frame, "0", 130)
        total = c.label(self.items_frame, "0", size=13, width=120)
        row = {"desc": desc, "qty": qty, "price": price, "total": total}
        delete = ctk.CTkButton(self.items_frame, text="✕", width=34, height=34, fg_color="transparent",
                               hover_color=c.SOFT, text_color=c.DANGER, command=lambda: self.remove_row(row))
        row["del"] = delete
        desc.grid(row=r, column=0, sticky="ew", padx=4, pady=3)
        qty.grid(row=r, column=1, padx=4)
        price.grid(row=r, column=2, padx=4)
        total.grid(row=r, column=3, padx=4)
        delete.grid(row=r, column=4)
        for e in (qty, price):
            e.bind("<KeyRelease>", lambda ev: self.recalc())
        self.rows.append(row)

    def remove_row(self, row):
        if len(self.rows) == 1:
            return
        for k in ("desc", "qty", "price", "total", "del"):
            row[k].destroy()
        self.rows.remove(row)
        self.recalc()

    def _items(self):
        return [{"desc": r["desc"].get(), "qty": r["qty"].get() or "0", "price": r["price"].get() or "0"}
                for r in self.rows]

    def recalc(self):
        cl = self.clients.get(self.client_cb.get(), {})
        cur = cl.get("currency", "FCFA")
        try:
            for r in self.rows:
                r["total"].configure(text=billing.money(billing.D(r["qty"].get() or 0) * billing.D(r["price"].get() or 0), cur, get_lang()))
            t = billing.compute_totals(self._items(), self.discount.get() or 0, self.tax.get() or 0)
            m = lambda v: billing.money(v, cur, get_lang())
            self.totals.configure(text=f"{c.tr('Sous-total')} : {m(t['subtotal'])}\n"
                                       f"{c.tr('Remise')} : - {m(t['discount'])}\n"
                                       f"{c.tr('Taxe')} : {m(t['tax'])}\n"
                                       f"{c.tr('TOTAL')} : {m(t['total'])}", text_color=c.TEXT)
        except (ValueError, ArithmeticError):
            self.totals.configure(text="Saisie invalide : utilisez uniquement des chiffres.", text_color=c.DANGER)

    # ---------------------------------------------------------------- action
    def generate(self):
        cl = self.clients.get(self.client_cb.get())
        if not cl:
            return c.error("Créez d'abord un entrepreneur dans l'onglet « Entrepreneurs ».", "Aucun entrepreneur")
        try:
            out, number, totals = billing.create_document(
                self.db, cl["id"], self.type_cb.get(),
                {"name": self.final_name.get(), "address": self.final_addr.get(), "phone": self.final_phone.get()},
                self._items(), self.discount.get() or 0, self.tax.get() or 0, self.notes.get("1.0", "end"), c.lang_code(self.doc_lang))
        except ValueError as e:
            return c.error(str(e), "Vérifiez le formulaire")
        self.app.pages["home"].refresh()
        self.show_list()
        if c.confirm(c.tr("{kind} {number} créé(e) et archivé(e).\nL'ouvrir maintenant ?", kind=c.tr(self.type_cb.get()), number=number), "Terminé"):
            c.open_path(out)

    def load_history(self):
        for w in self.history.winfo_children():
            w.destroy()
        cl = self.clients.get(self.f_client.get())
        typ = self.f_type.get()
        docs = self.db.search_documents(self.f_search.get(), "" if typ == "Tous" else typ, cl["id"] if cl else None)
        self.count_lbl.configure(text=c.tr("{n} document(s)", n=len(docs)))
        if not docs:
            c.subtitle(self.history, "Aucun document pour le moment.").pack(padx=8, pady=14, anchor="w")
        for d in docs:
            row = ctk.CTkFrame(self.history, fg_color=c.SOFT, corner_radius=8)
            row.pack(fill="x", pady=3)
            c.label(row, d["number"], bold=True, width=120).pack(side="left", padx=(12, 0), pady=9)
            c.label(row, c.fr_iso(d["issue_date"]), color=c.MUTED, width=90).pack(side="left")
            c.label(row, c.tr(d["doc_type"]), color=c.ACCENT, width=90).pack(side="left")
            c.label(row, f"{d['client_name']} → {d['final_client']}", width=300, wraplength=290).pack(side="left", padx=6)
            c.label(row, billing.money(Decimal(str(d["total"])), d["currency"], get_lang()), bold=True, width=140).pack(side="left")
            ctk.CTkButton(row, text="🗑", width=34, fg_color="transparent", hover_color=c.CARD, text_color=c.DANGER,
                          command=lambda i=d["id"]: self.delete_doc(i)).pack(side="right", padx=4)
            c.ghost_btn(row, "Dossier", lambda p=d["pdf_path"]: c.open_path(Path(p).parent), width=80).pack(side="right", padx=2)
            c.ghost_btn(row, "Ouvrir", lambda p=d["pdf_path"]: c.open_path(p), width=80).pack(side="right")

    def delete_doc(self, doc_id):
        if c.confirm("Retirer cette ligne de l'historique ?\n(Le fichier PDF reste sur votre ordinateur.)"):
            self.db.delete_document(doc_id)
            self.load_history()
            self.app.pages["home"].refresh()
