"""SecretariatPro — W Design. Point d'entrée de l'application."""
import logging
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from modules import security
from modules.db import Database
from modules.paths import app_data_dir, resource_path

logging.basicConfig(filename=str(app_data_dir() / "app.log"), level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")

LICENSE_CHECK_MS = 10 * 60 * 1000


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.init()
        ctk.set_appearance_mode(self.db.get_setting("theme", "light"))
        self.title("SecretariatPro — W Design")
        self.geometry("1180x760")
        self.minsize(1020, 660)
        self.configure(fg_color=("#F3F5F9", "#12161C"))
        try:
            self.iconbitmap(resource_path("assets/app.ico"))
        except tk.TclError:
            pass
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.current = None
        self._watch_id = None
        self.start()

    def report_callback_exception(self, exc, val, tb):
        logging.error("Erreur interface", exc_info=(exc, val, tb))
        messagebox.showerror("Erreur", "Une erreur inattendue est survenue.\n"
                                       "Le détail a été enregistré dans le journal de l'application.")

    def _swap(self, frame):
        if self.current is not None:
            self.current.destroy()
        self.current = frame
        frame.grid(row=0, column=0, sticky="nsew")

    # ---- enchaînement : licence → connexion → (mot de passe) → application
    def start(self):
        if self._watch_id:
            self.after_cancel(self._watch_id)
            self._watch_id = None
        from ui.auth_views import LoginView
        self._swap(LoginView(self, self.db, self.after_login))

    def after_login(self, must_change):
        if must_change:
            from ui.auth_views import ForcePasswordView
            return self._swap(ForcePasswordView(self, self.db, self.open_dashboard))
        self.open_dashboard()

    def open_dashboard(self):
        status = security.check_license()
        if not status.valid:
            from ui.auth_views import ActivationView
            return self._swap(ActivationView(self, status.reason, self.open_dashboard, self.db))
        from ui.dashboard import Dashboard
        self._swap(Dashboard(self, self.db, self.start))
        self._watch_id = self.after(LICENSE_CHECK_MS, self.watch_license)

    def watch_license(self):
        status = security.check_license()
        if not status.valid:
            messagebox.showwarning("Licence", status.reason)
            return self.start()
        if hasattr(self.current, "update_license_label"):
            self.current.update_license_label()
        self._watch_id = self.after(LICENSE_CHECK_MS, self.watch_license)


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception:
        logging.exception("Échec au démarrage")
        messagebox.showerror("SecretariatPro", "Impossible de démarrer l'application.")
        sys.exit(1)
