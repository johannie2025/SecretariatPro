"""À propos : présentation et contacts de W Design."""
import webbrowser

import customtkinter as ctk

from modules.version import APP_BUILD, APP_VERSION
from . import common as c


class AboutView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        box = c.card(body)
        box.pack(fill="x")
        ctk.CTkLabel(box, image=c.logo_image(420), text="").pack(pady=(24, 6))
        c.label(box, c.TAGLINE, bold=True, size=15, color=c.ACCENT).pack()
        c.subtitle(box, "L'architecture et l'innovation qui donnent vie à vos idées !").pack(pady=(2, 14))
        c.subtitle(box, "SecretariatPro est la solution bureautique de W Design : facturation, numérisation (OCR), "
                        "outils PDF, rédaction automatique, courrier et tâches — 100 % sur votre ordinateur, "
                        "sans abonnement ni envoi de données.", wraplength=620).pack(padx=30, pady=(0, 16))
        c.title(body, "Nous contacter", 20).pack(anchor="w", pady=(18, 6))
        for shown, digits in c.CONTACTS:
            row = c.card(body)
            row.pack(fill="x", pady=4)
            c.label(row, "📞  " + shown, bold=True, size=17).pack(side="left", padx=18, pady=16)
            c.primary_btn(row, "WhatsApp", lambda d=digits: webbrowser.open(f"https://wa.me/{d}"), width=130).pack(side="right", padx=(6, 14))
            c.ghost_btn(row, "Copier", lambda s=shown: c.copy_to_clipboard(self, s), width=90).pack(side="right")
        c.subtitle(body, "Le bouton WhatsApp ouvre votre navigateur ; l'application elle-même n'envoie aucune donnée.").pack(anchor="w", pady=(10, 0))
        c.subtitle(body, f"SecretariatPro v{APP_VERSION}  •  build {APP_BUILD}  •  © W Design").pack(anchor="w", pady=(6, 20))
