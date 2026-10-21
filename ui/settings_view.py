"""Paramètres : licence, mot de passe, apparence, à propos."""
import customtkinter as ctk

from modules import security
from . import common as c
from .auth_views import PasswordForm, DURATIONS, duration_selector


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        c.title(self, "Paramètres").pack(anchor="w")
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(10, 0))

        lic = c.card(body)
        lic.pack(fill="x", pady=(0, 12))
        c.label(lic, "Licence", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 2))
        self.status = c.label(lic, "", size=13)
        self.status.pack(anchor="w", padx=18)
        hw = ctk.CTkFrame(lic, fg_color=c.SOFT, corner_radius=10)
        hw.pack(fill="x", padx=18, pady=10)
        hwid = security.get_hwid()
        c.label(hw, "Code machine :", color=c.MUTED).pack(side="left", padx=(14, 6), pady=10)
        ctk.CTkLabel(hw, text=hwid, font=("Consolas", 16, "bold"), text_color=c.ACCENT).pack(side="left")
        c.ghost_btn(hw, "Copier", lambda: c.copy_to_clipboard(self, hwid), width=80).pack(side="right", padx=8)
        c.subtitle(lic, "Renouveler ce poste (la durée s'ajoute au temps restant) :").pack(anchor="w", padx=18)
        self.duration = duration_selector(lic)
        self.duration.pack(fill="x", padx=18, pady=6)
        c.primary_btn(lic, "Renouveler sur ce poste", self.renew_local, width=220).pack(anchor="w", padx=18, pady=(0, 10))
        c.subtitle(lic, "Ou collez une clé reçue de W Design :").pack(anchor="w", padx=18)
        self.key = ctk.CTkTextbox(lic, height=70, border_width=1, border_color=c.BORDER, font=("Consolas", 11))
        self.key.pack(fill="x", padx=18, pady=6)
        self.msg = c.label(lic, "", size=12)
        self.msg.pack(anchor="w", padx=18)
        c.primary_btn(lic, "Activer / renouveler", self.activate, width=200).pack(anchor="w", padx=18, pady=(4, 16))

        pw = c.card(body)
        pw.pack(fill="x", pady=(0, 12))
        c.label(pw, "Mot de passe administrateur", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 6))
        PasswordForm(pw, self.db, lambda: None).pack(anchor="w", padx=18, pady=(0, 16))

        ap = c.card(body)
        ap.pack(fill="x", pady=(0, 12))
        c.label(ap, "Apparence", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 6))
        seg = ctk.CTkSegmentedButton(ap, values=["Clair", "Sombre", "Système"], command=self.set_theme,
                                     selected_color=c.ACCENT, selected_hover_color=c.ACCENT_HOVER)
        seg.set({"light": "Clair", "dark": "Sombre", "system": "Système"}.get(self.db.get_setting("theme", "light"), "Clair"))
        seg.pack(anchor="w", padx=18, pady=(0, 16))

        ab = c.card(body)
        ab.pack(fill="x")
        ctk.CTkLabel(ab, image=c.logo_image(260), text="").pack(anchor="w", padx=18, pady=(14, 4))
        c.subtitle(ab, "SecretariatPro v1.0 — fonctionne 100 % hors-ligne, aucune donnée envoyée.").pack(anchor="w", padx=18)
        c.label(ab, c.CONTACT_LINE, bold=True, color=c.ACCENT).pack(anchor="w", padx=18, pady=(4, 14))
        self.refresh()

    def refresh(self):
        st = security.check_license()
        if st.valid:
            self.status.configure(text=f"Active jusqu'au {st.expires:%d/%m/%Y} ({st.days_left} jours restants)",
                                  text_color=c.SUCCESS if st.days_left > 7 else c.DANGER)
        else:
            self.status.configure(text=st.reason, text_color=c.DANGER)

    def renew_local(self):
        days = DURATIONS[self.duration.get()]
        ok, msg = security.activate_local(days)
        self.msg.configure(text=msg, text_color=c.SUCCESS if ok else c.DANGER)
        if ok:
            self.db.log_activation(days, "admin-local")
            self.refresh()

    def activate(self):
        ok, msg = security.activate_license(self.key.get("1.0", "end"))
        self.msg.configure(text=msg, text_color=c.SUCCESS if ok else c.DANGER)
        if ok:
            self.key.delete("1.0", "end")
            self.refresh()

    def set_theme(self, value):
        mode = {"Clair": "light", "Sombre": "dark", "Système": "system"}[value]
        ctk.set_appearance_mode(mode)
        self.db.set_setting("theme", mode)
