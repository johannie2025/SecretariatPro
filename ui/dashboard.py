"""Fenêtre principale : navigation latérale + pages."""
import customtkinter as ctk

from modules import security
from . import common as c
from .billing_view import BillingView
from .clients_view import ClientsView
from .ocr_view import OcrView
from .settings_view import SettingsView
from .templates_view import TemplatesView


class HomeView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        c.title(self, "Bonjour 👋").pack(anchor="w")
        c.subtitle(self, "Que souhaitez-vous faire aujourd'hui ?").pack(anchor="w", pady=(0, 14))
        self.stats = ctk.CTkFrame(self, fg_color="transparent")
        self.stats.pack(fill="x")
        self.stats.grid_columnconfigure((0, 1, 2), weight=1, uniform="s")
        q = ctk.CTkFrame(self, fg_color="transparent")
        q.pack(fill="x", pady=18)
        q.grid_columnconfigure((0, 1), weight=1, uniform="q")
        actions = [("🧾  Créer une facture / un devis", "billing", "Pour vos entrepreneurs et leurs clients"),
                   ("📄  Remplir un modèle Word", "templates", "Les champs sont détectés automatiquement"),
                   ("🔍  Lire un scan ou un PDF", "ocr", "Extraction de texte locale et rapide"),
                   ("👥  Gérer les entrepreneurs", "clients", "Profils, logos, NIF, RCCM")]
        for i, (t, page, desc) in enumerate(actions):
            b = c.card(q)
            b.grid(row=i // 2, column=i % 2, sticky="ew", padx=6, pady=6)
            c.label(b, t, bold=True, size=15).pack(anchor="w", padx=18, pady=(16, 0))
            c.subtitle(b, desc).pack(anchor="w", padx=18)
            c.primary_btn(b, "Ouvrir", lambda p=page: app.show(p), width=110).pack(anchor="w", padx=18, pady=(10, 16))
        foot = c.card(self)
        foot.pack(fill="x")
        c.label(foot, "W Design — " + c.TAGLINE, bold=True).pack(anchor="w", padx=18, pady=(14, 0))
        c.label(foot, c.CONTACT_LINE, color=c.ACCENT, bold=True).pack(anchor="w", padx=18, pady=(2, 14))
        self.refresh()

    def refresh(self):
        for w in self.stats.winfo_children():
            w.destroy()
        s = self.db.stats()
        for i, (v, t) in enumerate([(s["clients"], "Entrepreneurs"), (s["docs"], "Documents créés"),
                                    (s["month_docs"], "Ce mois-ci")]):
            b = c.card(self.stats)
            b.grid(row=0, column=i, sticky="ew", padx=6)
            ctk.CTkLabel(b, text=str(v), font=(c.FONT, 34, "bold"), text_color=c.ACCENT).pack(anchor="w", padx=18, pady=(14, 0))
            c.subtitle(b, t).pack(anchor="w", padx=18, pady=(0, 14))


class Dashboard(ctk.CTkFrame):
    NAV = [("home", "🏠  Accueil"), ("billing", "🧾  Facturation"), ("templates", "📄  Modèles"),
           ("ocr", "🔍  OCR"), ("clients", "👥  Entrepreneurs"), ("settings", "⚙️  Paramètres")]

    def __init__(self, parent, db, on_logout):
        super().__init__(parent, fg_color=c.BG)
        self.db, self.on_logout = db, on_logout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        side = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=c.CARD)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        ctk.CTkLabel(side, image=c.logo_image(190), text="").pack(pady=(20, 18))
        self.buttons = {}
        for key, text in self.NAV:
            b = ctk.CTkButton(side, text=text, anchor="w", height=42, corner_radius=10, fg_color="transparent",
                              hover_color=c.SOFT, text_color=c.TEXT, font=(c.FONT, 14),
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=14, pady=2)
            self.buttons[key] = b
        c.ghost_btn(side, "Se déconnecter", on_logout, width=190).pack(side="bottom", pady=18)
        self.license_lbl = c.subtitle(side, "", wraplength=190)
        self.license_lbl.pack(side="bottom")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.pages = {}
        for key, cls in (("home", HomeView), ("billing", BillingView), ("templates", TemplatesView),
                         ("ocr", OcrView), ("clients", ClientsView), ("settings", SettingsView)):
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
