"""Courrier (registre entrant/sortant) et tâches / rappels."""
import csv
import shutil
from datetime import date
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from modules.paths import client_dir, data_root, safe_name
from . import common as c

STATUSES = ["À traiter", "En cours", "Traité", "Archivé"]
NONE = "— Aucun —"


class MailView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.attach = ""
        c.title(self, "Courrier & tâches").pack(anchor="w")
        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color=c.ACCENT,
                                   segmented_button_selected_hover_color=c.ACCENT_HOVER, fg_color=c.CARD)
        self.tabs.pack(fill="both", expand=True, pady=(8, 0))
        self.tabs.add("Registre du courrier")
        self.tabs.add("Tâches & rappels")
        self._build_mail(self.tabs.tab("Registre du courrier"))
        self._build_tasks(self.tabs.tab("Tâches & rappels"))

    def _client_names(self):
        return [NONE] + [cl["name"] for cl in self.db.list_clients()]

    def _client_id(self, name):
        return next((cl["id"] for cl in self.db.list_clients() if cl["name"] == name), None)

    def refresh(self):
        names = self._client_names()
        for cb in (self.m_client, self.t_client):
            cb.configure(values=names)
            if cb.get() not in names:
                cb.set(NONE)
        self.load_mails()
        self.load_tasks()

    # ----------------------------------------------------------------- courrier
    def _build_mail(self, tab):
        form = self.m_form = ctk.CTkFrame(tab, fg_color="transparent")   # affiché seulement après « Nouveau courrier »
        self.m_dir = ctk.CTkSegmentedButton(form, values=["Entrant", "Sortant"], selected_color=c.ACCENT,
                                            selected_hover_color=c.ACCENT_HOVER)
        self.m_dir.set("Entrant")
        self.m_dir.grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.m_date = c.entry(form, "JJ/MM/AAAA", 120)
        self.m_date.insert(0, date.today().strftime("%d/%m/%Y"))
        self.m_date.grid(row=0, column=1, padx=4)
        self.m_party = c.entry(form, "Correspondant (expéditeur / destinataire)", 280)
        self.m_party.grid(row=0, column=2, padx=4)
        self.m_client = ctk.CTkComboBox(form, values=[NONE], width=200, height=38, state="readonly")
        self.m_client.set(NONE)
        self.m_client.grid(row=0, column=3, padx=4)
        self.m_subject = c.entry(form, "Objet du courrier", 420)
        self.m_subject.grid(row=1, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
        self.m_file = c.ghost_btn(form, "Joindre un fichier...", self.pick_attach, width=200)
        self.m_file.grid(row=1, column=3, padx=4)
        c.primary_btn(form, "Enregistrer", self.add_mail, width=120).grid(row=1, column=4, padx=4)
        c.ghost_btn(form, "Annuler", lambda: self.toggle_mail_form(False), width=90).grid(row=1, column=5, padx=4)
        bar = self.m_bar = ctk.CTkFrame(tab, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 2))
        c.primary_btn(bar, "+  Nouveau courrier", lambda: self.toggle_mail_form(True), width=200).pack(side="right", padx=(8, 0))
        self.m_search = c.entry(bar, "Rechercher (n°, correspondant, objet...)", 340)
        self.m_search.pack(side="left")
        self.m_search.bind("<KeyRelease>", lambda e: self.load_mails())
        c.ghost_btn(bar, "Exporter en CSV", self.export_csv, width=150).pack(side="right")
        self.m_list = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.m_list.pack(fill="both", expand=True)

    def toggle_mail_form(self, show):
        if show:
            self.m_form.pack(fill="x", before=self.m_bar)
        else:
            self.m_form.pack_forget()

    def pick_attach(self):
        f = filedialog.askopenfilename()
        if f:
            self.attach = f
            self.m_file.configure(text=Path(f).name[:24])

    def add_mail(self):
        try:
            iso = c.parse_date(self.m_date.get()) or date.today().isoformat()
            name = self.m_client.get()
            cid = self._client_id(name)
            stored = ""
            if self.attach and Path(self.attach).is_file():
                folder = client_dir(name, "Courrier") if cid else data_root() / "Courrier"
                folder.mkdir(parents=True, exist_ok=True)
                dest = c.unique_path(folder / f"{iso}_{safe_name(Path(self.attach).stem)}{Path(self.attach).suffix.lower()}")
                shutil.copyfile(self.attach, dest)
                stored = str(dest)
            ref = self.db.add_mail(self.m_dir.get(), iso, self.m_party.get(), self.m_subject.get(), cid, "À traiter", stored)
        except ValueError as e:
            return c.error(str(e))
        for e in (self.m_party, self.m_subject):
            e.delete(0, "end")
        self.attach = ""
        self.m_file.configure(text="Joindre un fichier...")
        self.toggle_mail_form(False)
        self.load_mails()
        c.info(f"Courrier enregistré sous le n° {ref}.")

    def load_mails(self):
        for w in self.m_list.winfo_children():
            w.destroy()
        rows = self.db.list_mails(self.m_search.get())
        if not rows:
            c.subtitle(self.m_list, "Aucun courrier enregistré.").pack(anchor="w", padx=8, pady=10)
        for m in rows:
            row = ctk.CTkFrame(self.m_list, fg_color=c.SOFT, corner_radius=8)
            row.pack(fill="x", pady=3)
            c.label(row, m["ref"], bold=True, width=110).pack(side="left", padx=(10, 0), pady=8)
            c.label(row, c.fr_iso(m["mail_date"]), color=c.MUTED, width=90).pack(side="left")
            c.label(row, f"{m['party']} — {m['subject']}", width=330, wraplength=320).pack(side="left", padx=6)
            ctk.CTkButton(row, text="🗑", width=34, fg_color="transparent", hover_color=c.CARD, text_color=c.DANGER,
                          command=lambda i=m["id"]: self.del_mail(i)).pack(side="right", padx=4)
            if m["file_path"]:
                c.ghost_btn(row, "Ouvrir", lambda p=m["file_path"]: c.open_path(p), width=70).pack(side="right")
            cb = ctk.CTkComboBox(row, values=STATUSES, width=120, height=32, state="readonly",
                                 command=lambda v, i=m["id"]: self.db.set_mail_status(i, v))
            cb.set(m["status"])
            cb.pack(side="right", padx=6)

    def del_mail(self, mail_id):
        if c.confirm("Supprimer cette ligne du registre ?"):
            self.db.delete_mail(mail_id)
            self.load_mails()

    def export_csv(self):
        f = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="registre_courrier.csv",
                                         filetypes=[("CSV (Excel)", "*.csv")])
        if not f:
            return
        with open(f, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow([c.tr(x) for x in ("N°", "Type", "Date", "Correspondant", "Objet", "Entrepreneur", "Statut")])
            for m in self.db.list_mails("", 100000):
                w.writerow([m["ref"], c.tr(m["direction"]), c.fr_iso(m["mail_date"]), m["party"], m["subject"],
                            m["client_name"] or "", c.tr(m["status"])])
        c.info("Registre exporté (ouvrable dans Excel).")

    # ------------------------------------------------------------------- tâches
    def _build_tasks(self, tab):
        form = self.t_form = ctk.CTkFrame(tab, fg_color="transparent")   # affiché seulement après « Nouvelle tâche »
        self.t_title = c.entry(form, "Tâche à faire (ex. Appeler M. Obiang)", 380)
        self.t_title.grid(row=0, column=0, padx=4, pady=4)
        self.t_due = c.entry(form, "Échéance JJ/MM/AAAA", 160)
        self.t_due.grid(row=0, column=1, padx=4)
        self.t_client = ctk.CTkComboBox(form, values=[NONE], width=200, height=38, state="readonly")
        self.t_client.set(NONE)
        self.t_client.grid(row=0, column=2, padx=4)
        c.primary_btn(form, "Ajouter", self.add_task, width=110).grid(row=0, column=3, padx=4)
        c.ghost_btn(form, "Annuler", lambda: self.toggle_task_form(False), width=90).grid(row=0, column=4, padx=4)
        tbar = self.t_bar = ctk.CTkFrame(tab, fg_color="transparent")
        tbar.pack(fill="x", pady=6)
        c.primary_btn(tbar, "+  Nouvelle tâche", lambda: self.toggle_task_form(True), width=190).pack(side="right")
        self.t_done = ctk.CTkSwitch(tbar, text="Afficher les tâches terminées", command=self.load_tasks,
                                    progress_color=c.ACCENT)
        self.t_done.pack(side="left")
        self.t_list = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.t_list.pack(fill="both", expand=True)

    def toggle_task_form(self, show):
        if show:
            self.t_form.pack(fill="x", before=self.t_bar)
        else:
            self.t_form.pack_forget()

    def add_task(self):
        try:
            self.db.add_task(self.t_title.get(), c.parse_date(self.t_due.get()), self._client_id(self.t_client.get()))
        except ValueError as e:
            return c.error(str(e))
        self.t_title.delete(0, "end")
        self.t_due.delete(0, "end")
        self.toggle_task_form(False)
        self.load_tasks()
        self.app.pages["home"].refresh()

    def load_tasks(self):
        for w in self.t_list.winfo_children():
            w.destroy()
        rows = self.db.list_tasks(bool(self.t_done.get()))
        if not rows:
            c.subtitle(self.t_list, "Rien à faire pour le moment 🎉").pack(anchor="w", padx=8, pady=10)
        today = date.today().isoformat()
        for t in rows:
            row = ctk.CTkFrame(self.t_list, fg_color=c.SOFT, corner_radius=8)
            row.pack(fill="x", pady=3)
            late = bool(t["due_date"]) and t["due_date"] < today and not t["done"]
            cb = ctk.CTkCheckBox(row, text=t["title"], font=(c.FONT, 13), fg_color=c.ACCENT,
                                 command=lambda i=t["id"], v=t["done"]: self.toggle(i, not v))
            if t["done"]:
                cb.select()
            cb.pack(side="left", padx=12, pady=10)
            if t["due_date"]:
                c.label(row, ("⚠ " if late else "") + c.fr_iso(t["due_date"]), color=c.DANGER if late else c.MUTED).pack(side="left", padx=8)
            if t["client_name"]:
                c.label(row, t["client_name"], color=c.MUTED).pack(side="left")
            ctk.CTkButton(row, text="🗑", width=34, fg_color="transparent", hover_color=c.CARD, text_color=c.DANGER,
                          command=lambda i=t["id"]: self.del_task(i)).pack(side="right", padx=6)

    def toggle(self, task_id, done):
        self.db.set_task_done(task_id, done)
        self.load_tasks()
        self.app.pages["home"].refresh()

    def del_task(self, task_id):
        self.db.delete_task(task_id)
        self.load_tasks()
        self.app.pages["home"].refresh()
