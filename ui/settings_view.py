"""Paramètres : licence, mot de passe, apparence, à propos."""
from datetime import date
from tkinter import filedialog

import customtkinter as ctk

from modules import backup, i18n, security
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
        self.lic_card = lic
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

        lg = c.card(body)
        lg.pack(fill="x", pady=(0, 12))
        c.label(lg, "Langue", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 6))
        lseg = ctk.CTkSegmentedButton(lg, values=[i18n.LANG_NAMES[x] for x in i18n.LANGS], command=self.set_language,
                                      selected_color=c.ACCENT, selected_hover_color=c.ACCENT_HOVER)
        lseg.set(i18n.LANG_NAMES[i18n.get_lang()])
        lseg.pack(anchor="w", padx=18, pady=(0, 16))

        bk = c.card(body)
        self.bk_card = bk
        bk.pack(fill="x", pady=(0, 12))
        c.label(bk, "Sauvegarde des données", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 2))
        c.subtitle(bk, "Base de données + tous les documents des entrepreneurs, dans un seul fichier .zip.",
                   wraplength=560).pack(anchor="w", padx=18)
        row = ctk.CTkFrame(bk, fg_color="transparent")
        row.pack(anchor="w", padx=18, pady=(8, 16))
        c.primary_btn(row, "Sauvegarder", self.do_backup, width=150).pack(side="left")
        c.ghost_btn(row, "Restaurer...", self.do_restore, width=150).pack(side="left", padx=8)

        ab = c.card(body)
        ab.pack(fill="x")
        ctk.CTkLabel(ab, image=c.logo_image(260), text="").pack(anchor="w", padx=18, pady=(14, 4))
        c.subtitle(ab, "SecretariatPro v1.1 — fonctionne 100 % hors-ligne, aucune donnée envoyée.").pack(anchor="w", padx=18)
        c.label(ab, c.CONTACT_LINE, bold=True, color=c.ACCENT).pack(anchor="w", padx=18, pady=(4, 14))
        if self.db.is_admin():
            self._build_users(body)
        else:                              # le secrétariat ne gère ni licence, ni sauvegardes, ni comptes
            self.lic_card.pack_forget()
            self.bk_card.pack_forget()
            c.subtitle(body, "Licence, sauvegardes et comptes : réservés à l'administrateur.").pack(anchor="w", pady=(0, 12))
        self.refresh()

    # ------------------------------------------------------------- comptes
    def _build_users(self, body):
        card = c.card(body)
        card.pack(fill="x", pady=(0, 12))
        c.label(card, "Comptes utilisateurs", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 2))
        c.subtitle(card, "Créez un compte pour chaque employé du secrétariat : il pourra travailler mais pas gérer "
                         "la licence, les sauvegardes ni les comptes.", wraplength=620).pack(anchor="w", padx=18)
        self.users_box = ctk.CTkFrame(card, fg_color="transparent")
        self.users_box.pack(fill="x", padx=14, pady=8)
        c.primary_btn(card, "+  Nouveau compte", lambda: self.toggle_user_form(True), width=190).pack(anchor="w", padx=18, pady=(0, 14))
        form = self.u_form = ctk.CTkFrame(card, fg_color="transparent")   # affiché après « Nouveau compte »
        self.u_anchor = card
        self.u_name = c.entry(form, "Nom d'utilisateur", 170)
        self.u_name.grid(row=0, column=0, padx=4, pady=4)
        self.u_pwd = c.entry(form, "Mot de passe provisoire", 190, show="•")
        self.u_pwd.grid(row=0, column=1, padx=4)
        self.u_role = ctk.CTkSegmentedButton(form, values=["Secrétariat", "Administrateur"], selected_color=c.ACCENT,
                                             selected_hover_color=c.ACCENT_HOVER)
        self.u_role.set("Secrétariat")
        self.u_role.grid(row=0, column=2, padx=4)
        c.primary_btn(form, "Créer le compte", self.create_user, width=150).grid(row=0, column=3, padx=4)
        c.ghost_btn(form, "Annuler", lambda: self.toggle_user_form(False), width=90).grid(row=0, column=4, padx=4)
        self.load_users()

    def toggle_user_form(self, show):
        if show:
            self.u_form.pack(fill="x", padx=14, pady=(0, 16))
        else:
            self.u_form.pack_forget()

    def load_users(self):
        for w in self.users_box.winfo_children():
            w.destroy()
        for u in self.db.list_users():
            row = ctk.CTkFrame(self.users_box, fg_color=c.SOFT, corner_radius=8)
            row.pack(fill="x", pady=3)
            c.label(row, u["username"], bold=True, width=150).pack(side="left", padx=(12, 0), pady=8)
            c.label(row, "Administrateur" if u["role"] == "admin" else "Secrétariat", color=c.MUTED, width=120).pack(side="left")
            c.label(row, "Actif" if u["active"] else "Désactivé", color=c.SUCCESS if u["active"] else c.DANGER, width=90).pack(side="left")
            ctk.CTkButton(row, text="🗑", width=34, fg_color="transparent", hover_color=c.CARD, text_color=c.DANGER,
                          command=lambda x=u: self.delete_user(x)).pack(side="right", padx=4)
            c.ghost_btn(row, "Désactiver" if u["active"] else "Activer", lambda x=u: self.toggle_user(x), width=110).pack(side="right")
            c.ghost_btn(row, "Réinitialiser le mot de passe", lambda x=u: self.reset_user(x), width=210).pack(side="right", padx=6)

    def create_user(self):
        role = "admin" if self.u_role.get() == "Administrateur" else "secretariat"
        try:
            self.db.create_user(self.u_name.get(), self.u_pwd.get(), role)
        except ValueError as e:
            return c.error(str(e))
        self.u_name.delete(0, "end")
        self.u_pwd.delete(0, "end")
        self.toggle_user_form(False)
        self.load_users()
        c.info("Compte créé. L'utilisateur devra changer son mot de passe à la première connexion.")

    def reset_user(self, u):
        pwd = ctk.CTkInputDialog(text=c.tr("Nouveau mot de passe provisoire pour {name} :", name=u["username"]),
                                 title="Réinitialiser le mot de passe").get_input()
        if pwd:
            try:
                self.db.reset_password(u["id"], pwd)
            except ValueError as e:
                return c.error(str(e))
            c.info(c.tr("Mot de passe réinitialisé : {name} devra en choisir un nouveau à sa prochaine connexion.", name=u["username"]))

    def toggle_user(self, u):
        try:
            self.db.set_user_active(u["id"], not u["active"])
        except ValueError as e:
            return c.error(str(e))
        self.load_users()

    def delete_user(self, u):
        if c.confirm(c.tr("Supprimer le compte {name} ?", name=u["username"])):
            try:
                self.db.delete_user(u["id"])
            except ValueError as e:
                return c.error(str(e))
            self.load_users()

    def refresh(self):
        st = security.check_license()
        if st.valid:
            self.status.configure(text=f"Active jusqu'au {st.expires:%d/%m/%Y} ({st.days_left} jours restants)",
                                  text_color=c.SUCCESS if st.days_left > 7 else c.DANGER)
        else:
            self.status.configure(text=st.reason, text_color=c.DANGER)

    def do_backup(self):
        f = filedialog.asksaveasfilename(defaultextension=".zip", initialfile=f"SecretariatPro_sauvegarde_{date.today()}.zip",
                                         filetypes=[("Sauvegarde", "*.zip")])
        if f:
            try:
                backup.make_backup(self.db, f)
            except Exception as e:  # noqa: BLE001
                return c.user_error(e)
            c.info("Sauvegarde terminée. Conservez-la sur une clé USB ou un autre ordinateur.")

    def do_restore(self):
        f = filedialog.askopenfilename(filetypes=[("Sauvegarde", "*.zip")])
        if f and c.confirm("Restaurer cette sauvegarde ?\nLes données actuelles seront remplacées."):
            try:
                backup.restore_backup(self.db, f)
            except Exception as e:  # noqa: BLE001
                return c.user_error(e)
            c.info("Restauration terminée. Fermez puis rouvrez l'application.")

    def renew_local(self):
        days = DURATIONS[self.duration.get()]
        ok, msg = security.activate_local(days)
        self.msg.configure(text=msg, text_color=c.SUCCESS if ok else c.DANGER)
        if ok:
            try:
                self.db.log_activation(days, "admin-local")
            except Exception:  # noqa: BLE001
                pass
            self.refresh()

    def activate(self):
        ok, msg = security.activate_license(self.key.get("1.0", "end"))
        self.msg.configure(text=msg, text_color=c.SUCCESS if ok else c.DANGER)
        if ok:
            self.key.delete("1.0", "end")
            self.refresh()

    def set_language(self, name):
        code = next(k for k, v in i18n.LANG_NAMES.items() if v == name)
        i18n.set_lang(code)
        self.db.set_setting("lang", code)
        self.app.rebuild()

    def set_theme(self, value):
        mode = {"Clair": "light", "Sombre": "dark", "Système": "system"}[value]
        ctk.set_appearance_mode(mode)
        self.db.set_setting("theme", mode)
