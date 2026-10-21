"""Écrans d'activation de licence, de connexion et de changement de mot de passe."""
import customtkinter as ctk

from modules import security
from . import common as c


def _center_card(parent, width=440):
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)
    box = c.card(parent, width=width)
    box.grid(row=0, column=0, padx=20, pady=20)
    inner = ctk.CTkFrame(box, fg_color="transparent")
    inner.pack(padx=36, pady=32)
    ctk.CTkLabel(inner, image=c.logo_image(300), text="").pack(pady=(0, 6))
    return inner


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, db, on_success):
        super().__init__(parent, fg_color=c.BG)
        self.db, self.on_success = db, on_success
        inner = _center_card(self)
        c.title(inner, "Connexion", 22).pack(anchor="w", pady=(14, 0))
        c.subtitle(inner, "Accédez à votre espace de secrétariat.").pack(anchor="w", pady=(0, 14))
        b1, self.user = c.labeled_entry(inner, "Identifiant", "admin", 320)
        b1.pack(fill="x", pady=4)
        b2, self.pwd = c.labeled_entry(inner, "Mot de passe", "••••••••", 320, show="•")
        b2.pack(fill="x", pady=4)
        self.msg = c.label(inner, "", color=c.DANGER, size=12, wraplength=320)
        self.msg.pack(anchor="w", pady=(6, 0))
        c.primary_btn(inner, "Se connecter", self.submit, width=320).pack(pady=(10, 0))
        c.subtitle(inner, c.CONTACT_LINE).pack(pady=(18, 0))
        self.user.insert(0, "admin")
        self.pwd.focus_set()
        self.pwd.bind("<Return>", lambda e: self.submit())
        self.user.bind("<Return>", lambda e: self.submit())

    def submit(self):
        ok, msg, must_change = self.db.authenticate(self.user.get(), self.pwd.get())
        if ok:
            self.on_success(must_change)
        else:
            self.msg.configure(text=msg)
            self.pwd.delete(0, "end")


DURATIONS = {"1 mois": 30, "3 mois": 90, "6 mois": 180, "1 an": 365}


def duration_selector(parent):
    seg = ctk.CTkSegmentedButton(parent, values=list(DURATIONS), height=40,
                                 selected_color=c.ACCENT, selected_hover_color=c.ACCENT_HOVER)
    seg.set("1 mois")
    return seg


class ActivationView(ctk.CTkFrame):
    """Affichée après la connexion admin quand la licence du poste est absente ou expirée."""

    def __init__(self, parent, reason, on_success, db):
        super().__init__(parent, fg_color=c.BG)
        self.on_success, self.db = on_success, db
        inner = _center_card(self, 520)
        c.title(inner, "Activer ce poste", 22).pack(anchor="w", pady=(14, 0))
        c.label(inner, reason, color=c.DANGER, size=13, wraplength=440).pack(anchor="w", pady=(2, 10))
        c.subtitle(inner, "Choisissez la durée de la licence pour cet ordinateur :").pack(anchor="w", pady=(0, 6))
        self.duration = duration_selector(inner)
        self.duration.pack(fill="x")
        self.msg = c.label(inner, "", size=12, color=c.DANGER, wraplength=440)
        self.msg.pack(anchor="w", pady=(8, 0))
        c.primary_btn(inner, "Activer sur ce poste", self.activate_local, width=440).pack(pady=(6, 0))
        c.subtitle(inner, "—  ou activation à distance avec une clé  —").pack(pady=(16, 4))
        row = ctk.CTkFrame(inner, fg_color=c.SOFT, corner_radius=10)
        row.pack(fill="x", pady=4)
        hwid = security.get_hwid()
        ctk.CTkLabel(row, text=hwid, font=("Consolas", 16, "bold"), text_color=c.ACCENT).pack(
            side="left", padx=14, pady=8)
        c.ghost_btn(row, "Copier", lambda: c.copy_to_clipboard(self, hwid), width=80).pack(side="right", padx=8)
        self.key = ctk.CTkTextbox(inner, height=60, width=440, corner_radius=8, border_width=1,
                                  border_color=c.BORDER, font=("Consolas", 11))
        self.key.pack(fill="x", pady=4)
        c.ghost_btn(inner, "Activer avec la clé", self.activate_key, width=440).pack()
        c.subtitle(inner, c.CONTACT_LINE).pack(pady=(14, 0))

    def _done(self, ok, msg, days, mode):
        self.msg.configure(text=msg, text_color=c.SUCCESS if ok else c.DANGER)
        if ok:
            self.db.log_activation(days, mode)
            self.after(900, self.on_success)

    def activate_local(self):
        days = DURATIONS[self.duration.get()]
        ok, msg = security.activate_local(days)
        self._done(ok, msg, days, "admin-local")

    def activate_key(self):
        ok, msg = security.activate_license(self.key.get("1.0", "end"))
        self._done(ok, msg, 0, "cle")


class PasswordForm(ctk.CTkFrame):
    """Formulaire de changement de mot de passe (réutilisé dans les paramètres)."""

    def __init__(self, parent, db, on_done, transparent=False):
        super().__init__(parent, fg_color="transparent")
        self.db, self.on_done = db, on_done
        b1, self.p1 = c.labeled_entry(self, "Nouveau mot de passe", "10 caractères minimum", 320, show="•")
        b1.pack(fill="x", pady=4)
        b2, self.p2 = c.labeled_entry(self, "Confirmer le mot de passe", "", 320, show="•")
        b2.pack(fill="x", pady=4)
        c.subtitle(self, "Majuscules, minuscules, chiffre et symbole requis.").pack(anchor="w")
        self.msg = c.label(self, "", size=12, color=c.DANGER, wraplength=320)
        self.msg.pack(anchor="w", pady=4)
        c.primary_btn(self, "Enregistrer", self.save, width=320).pack(pady=(4, 0))

    def save(self):
        err = security.password_policy_error(self.p1.get())
        if err:
            return self.msg.configure(text=err, text_color=c.DANGER)
        if self.p1.get() != self.p2.get():
            return self.msg.configure(text="Les deux mots de passe sont différents.", text_color=c.DANGER)
        self.db.change_password(self.p1.get())
        self.p1.delete(0, "end")
        self.p2.delete(0, "end")
        self.msg.configure(text="Mot de passe mis à jour.", text_color=c.SUCCESS)
        self.on_done()


class ForcePasswordView(ctk.CTkFrame):
    def __init__(self, parent, db, on_done):
        super().__init__(parent, fg_color=c.BG)
        inner = _center_card(self)
        c.title(inner, "Sécurisez votre compte", 22).pack(anchor="w", pady=(14, 0))
        c.subtitle(inner, "Première connexion : choisissez votre propre mot de passe.",
                   wraplength=320).pack(anchor="w", pady=(0, 10))
        PasswordForm(inner, db, lambda: self.after(600, on_done)).pack()
