"""Facturation : devis, proforma et factures pour les clients des entrepreneurs."""
from decimal import Decimal

import customtkinter as ctk

from modules import billing
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
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        body.grid_columnconfigure(0, weight=1)

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

        c.label(body, "Historique récent", bold=True, size=15).grid(row=4, column=0, sticky="w", pady=(6, 4))
        self.history = c.card(body)
        self.history.grid(row=5, column=0, sticky="ew")
        self.refresh()

    def _lbl(self, parent, text, r, col):
        c.label(parent, text, bold=True, size=12, color=c.MUTED).grid(row=r, column=col, sticky="w", padx=14, pady=(12, 3))

    # -------------------------------------------------------------- données
    def refresh(self):
        self.clients = {cl["name"]: cl for cl in self.db.list_clients()}
        names = list(self.clients) or [""]
        self.client_cb.configure(values=names)
        if self.client_cb.get() not in self.clients:
            self.client_cb.set(names[0])
        self.on_client()
        if not self.rows:
            self.add_row()
        self.load_history()

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
                r["total"].configure(text=billing.money(billing.D(r["qty"].get() or 0) * billing.D(r["price"].get() or 0), cur))
            t = billing.compute_totals(self._items(), self.discount.get() or 0, self.tax.get() or 0)
            self.totals.configure(text=f"Sous-total : {billing.money(t['subtotal'], cur)}\n"
                                       f"Remise : - {billing.money(t['discount'], cur)}\n"
                                       f"Taxe : {billing.money(t['tax'], cur)}\n"
                                       f"TOTAL : {billing.money(t['total'], cur)}", text_color=c.TEXT)
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
                self._items(), self.discount.get() or 0, self.tax.get() or 0, self.notes.get("1.0", "end"))
        except ValueError as e:
            return c.error(str(e), "Vérifiez le formulaire")
        self.load_history()
        self.app.pages["home"].refresh()
        if c.confirm(f"{self.type_cb.get()} {number} créé(e) et archivé(e).\nL'ouvrir maintenant ?", "Terminé"):
            c.open_path(out)

    def load_history(self):
        for w in self.history.winfo_children():
            w.destroy()
        docs = self.db.list_documents(limit=15)
        if not docs:
            c.subtitle(self.history, "Aucun document pour le moment.").pack(padx=16, pady=16, anchor="w")
        for d in docs:
            row = ctk.CTkFrame(self.history, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            c.label(row, f"{d['number']}", bold=True, width=130).pack(side="left")
            c.label(row, f"{d['client_name']} → {d['final_client']}", color=c.MUTED, width=330).pack(side="left")
            c.label(row, billing.money(Decimal(str(d["total"])), d["currency"]), width=150).pack(side="left")
            c.ghost_btn(row, "Ouvrir", lambda p=d["pdf_path"]: c.open_path(p), width=80).pack(side="right")
