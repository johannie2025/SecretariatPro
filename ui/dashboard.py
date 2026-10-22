"""Fenêtre principale : navigation latérale + pages."""
import customtkinter as ctk

from modules import security
from . import common as c
from .about_view import AboutView
from .billing_view import BillingView
from .clients_view import ClientsView
from .mail_view import MailView
from .ocr_view import OcrView
from .pdf_view import PdfView
from .settings_view import SettingsView
from .templates_view import TemplatesView
from .writer_view import WriterView


class HomeView(ctk.CTkFrame):
    ACTIONS = [("🧾  Facturation", "billing", "Factures, devis, proformas"),
               ("📄  Modèles Word", "templates", "Champs détectés automatiquement"),
               ("🔍  Numérisation", "ocr", "Scan → Word / PDF avec mise en page"),
               ("📑  Outils PDF", "pdf", "Éditer, fusionner, signer, protéger"),
               ("✍️  Rédaction", "writer", "Lettres, attestations, mise en forme auto"),
               ("📬  Courrier & tâches", "mail", "Registre, rappels, échéances"),
               ("👥  Entrepreneurs", "clients", "Profils, logos, NIF, RCCM"),
               ("ℹ️  À propos", "about", "Contacts W Design")]

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        c.title(body, "Bonjour 👋").pack(anchor="w")
        c.subtitle(body, "Que souhaitez-vous faire aujourd'hui ?").pack(anchor="w", pady=(0, 12))
        self.stats = ctk.CTkFrame(body, fg_color="transparent")
        self.stats.pack(fill="x")
        self.stats.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="s")
        q = ctk.CTkFrame(body, fg_color="transparent")
        q.pack(fill="x", pady=14)
        q.grid_columnconfigure((0, 1, 2), weight=1, uniform="q")
        for i, (t, page, desc) in enumerate(self.ACTIONS):
            b = c.card(q)
            b.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            c.label(b, t, bold=True, size=14).pack(anchor="w", padx=16, pady=(14, 0))
            c.subtitle(b, desc, wraplength=190).pack(anchor="w", padx=16)
            c.primary_btn(b, "Ouvrir", lambda p=page: app.show(p), width=100).pack(anchor="w", padx=16, pady=(8, 14))
        foot = c.card(body)
        foot.pack(fill="x")
        c.label(foot, "W Design — " + c.TAGLINE, bold=True).pack(anchor="w", padx=18, pady=(14, 0))
        c.label(foot, c.CONTACT_LINE, color=c.ACCENT, bold=True).pack(anchor="w", padx=18, pady=(2, 14))
        self.refresh()

    def refresh(self):
        for w in self.stats.winfo_children():
            w.destroy()
        s, t = self.db.stats(), self.db.task_counts()
        late = f"dont {t['late']} en retard" if t["late"] else (f"{t['today']} pour aujourd'hui" if t["today"] else "Tâches ouvertes")
        for i, (v, txt, warn) in enumerate([(s["clients"], "Entrepreneurs", False), (s["docs"], "Documents créés", False),
                                            (s["month_docs"], "Ce mois-ci", False), (t["open"], late, bool(t["late"]))]):
            b = c.card(self.stats)
            b.grid(row=0, column=i, sticky="ew", padx=5)
            ctk.CTkLabel(b, text=str(v), font=(c.FONT, 32, "bold"), text_color=c.DANGER if warn else c.ACCENT).pack(anchor="w", padx=16, pady=(12, 0))
            c.subtitle(b, txt).pack(anchor="w", padx=16, pady=(0, 12))


class Dashboard(ctk.CTkFrame):
    NAV = [("home", "🏠  Accueil"), ("billing", "🧾  Facturation"), ("templates", "📄  Modèles Word"),
           ("ocr", "🔍  Numérisation"), ("pdf", "📑  Outils PDF"), ("writer", "✍️  Rédaction"),
           ("mail", "📬  Courrier & tâches"), ("clients", "👥  Entrepreneurs"), ("settings", "⚙️  Paramètres"),
           ("about", "ℹ️  À propos")]

    def __init__(self, parent, db, on_logout, rebuild=None):
        super().__init__(parent, fg_color=c.BG)
        self.db, self.on_logout = db, on_logout
        self.rebuild = rebuild or (lambda: None)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        side = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=c.CARD)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        ctk.CTkLabel(side, image=c.logo_image(190), text="").pack(pady=(16, 12))
        self.buttons = {}
        for key, text in self.NAV:
            b = ctk.CTkButton(side, text=text, anchor="w", height=36, corner_radius=10, fg_color="transparent",
                              hover_color=c.SOFT, text_color=c.TEXT, font=(c.FONT, 14),
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=1)
            self.buttons[key] = b
        c.ghost_btn(side, "Se déconnecter", on_logout, width=190).pack(side="bottom", pady=18)
        self.license_lbl = c.subtitle(side, "", wraplength=190)
        self.license_lbl.pack(side="bottom")
        u = db.current_user or {"username": "", "role": "admin"}
        c.subtitle(side, c.tr("Connecté : {name} ({role})", name=u["username"],
                              role=c.tr("Administrateur" if u["role"] == "admin" else "Secrétariat")),
                   wraplength=190).pack(side="bottom", pady=(0, 4))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.pages = {}
        for key, cls in (("home", HomeView), ("billing", BillingView), ("templates", TemplatesView),
                         ("ocr", OcrView), ("pdf", PdfView), ("writer", WriterView), ("mail", MailView),
                         ("clients", ClientsView), ("settings", SettingsView), ("about", AboutView)):
            self.pages[key] = cls(self.content, self)
            self.pages[key].grid(row=0, column=0, sticky="nsew")
        self.show("home")
        self.update_license_label()

    def show(self, key):
        for k, b in self.buttons.items():
            b.configure(fg_color=c.SOFT if k == key else "transparent",
                        text_color=c.ACCENT if k == key else c.TEXT)
        page = self.pages[key]
        if hasattr(page, "refresh"):
            page.refresh()
        page.tkraise()

    def update_license_label(self):
        st = security.check_license()
        if st.valid:
            self.license_lbl.configure(text=f"Licence : {st.days_left} j restants",
                                       text_color=c.SUCCESS if st.days_left > 7 else c.DANGER)
