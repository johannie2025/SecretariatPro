"""Thème et composants réutilisables (style moderne, clair/sombre)."""
import os
import subprocess
import sys
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

from modules.paths import resource_path

ACCENT = ("#1F5FBF", "#3B82F6")
ACCENT_HOVER = ("#174A94", "#2563EB")
BG = ("#F3F5F9", "#12161C")
CARD = ("#FFFFFF", "#1B212B")
BORDER = ("#E2E6EE", "#2A3240")
TEXT = ("#111827", "#F3F4F6")
MUTED = ("#6B7280", "#9CA3AF")
DANGER = ("#DC2626", "#EF4444")
SUCCESS = ("#16A34A", "#22C55E")
SOFT = ("#EAF1FC", "#222C3B")

CONTACT_LINE = "WhatsApp : +240 222 886 007  •  +240 555 445 514"
TAGLINE = "Agence d'Architecture • Design • Innovation"
FONT = "Segoe UI"


def logo_image(width: int):
    img = Image.open(resource_path("assets/logo.jpg")).convert("RGB")
    h = int(img.height * width / img.width)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(width, h))


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14, border_width=1, border_color=BORDER, **kw)


def title(parent, text, size=24):
    return ctk.CTkLabel(parent, text=text, font=(FONT, size, "bold"), text_color=TEXT, anchor="w")


def subtitle(parent, text, **kw):
    return ctk.CTkLabel(parent, text=text, font=(FONT, 13), text_color=MUTED, anchor="w",
                        justify="left", **kw)


def label(parent, text, bold=False, size=13, color=TEXT, **kw):
    return ctk.CTkLabel(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                        text_color=color, anchor="w", **kw)


def primary_btn(parent, text, command, width=160, **kw):
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=40, corner_radius=10,
                         fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
                         font=(FONT, 13, "bold"), **kw)


def ghost_btn(parent, text, command, width=140, danger=False, **kw):
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=40, corner_radius=10,
                         fg_color="transparent", border_width=1, border_color=BORDER,
                         hover_color=SOFT, text_color=DANGER if danger else TEXT,
                         font=(FONT, 13), **kw)


def entry(parent, placeholder="", width=240, show=None, **kw):
    return ctk.CTkEntry(parent, placeholder_text=placeholder, width=width, height=38, corner_radius=8,
                        border_color=BORDER, fg_color=("#FFFFFF", "#12161C"), font=(FONT, 13),
                        show=show, **kw)


def labeled_entry(parent, text, placeholder="", width=240, show=None):
    box = ctk.CTkFrame(parent, fg_color="transparent")
    label(box, text, bold=True, size=12, color=MUTED).pack(anchor="w", pady=(0, 3))
    e = entry(box, placeholder, width, show)
    e.pack(anchor="w", fill="x")
    return box, e


def info(msg, title_="Information"):
    messagebox.showinfo(title_, msg)


def error(msg, title_="Une erreur est survenue"):
    messagebox.showerror(title_, msg)


def confirm(msg, title_="Confirmation"):
    return messagebox.askyesno(title_, msg)


def open_path(path):
    """Ouvre un fichier ou dossier avec l'application par défaut du système."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        error("Impossible d'ouvrir ce fichier.")


def copy_to_clipboard(widget, text):
    widget.clipboard_clear()
    widget.clipboard_append(text)
