"""Intelligence artificielle (administrateur) : IA locale, fournisseurs gratuits en ligne, ordre, pauses, OCR IA."""
import webbrowser
from datetime import datetime

import customtkinter as ctk

from modules import ai_cloud, ai_local, ai_manager, i18n
from . import common as c


class ProviderCard(ctk.CTkFrame):
    def __init__(self, parent, view, prov):
        super().__init__(parent, fg_color=c.CARD, corner_radius=14, border_width=1, border_color=c.BORDER)
        self.view, self.prov = view, prov
        self.models, self.sel_text, self.sel_ocr, self.open = [], {}, {}, False
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=14, pady=(10, 8))
        c.label(head, prov["name"], bold=True, size=15).pack(side="left")
        self.status = c.label(head, "", size=12)
        self.status.pack(side="left", padx=12)
        self.sw = ctk.CTkSwitch(head, text="Activé", progress_color=c.ACCENT, command=self.toggle)
        self.sw.pack(side="right")
        if prov["enabled"]:
            self.sw.select()
        self.btn = c.ghost_btn(head, "Configurer ▾", self.expand, width=130)
        self.btn.pack(side="right", padx=10)
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.update_status()

    # ---------------------------------------------------------------- état
    def update_status(self):
        pend = ai_cloud.next_available(self.prov["id"])
        if pend and not ai_cloud.candidates(self.prov):
            self.status.configure(text=c.tr("⏳ en pause jusqu'à {t}", t=datetime.fromtimestamp(pend).strftime("%H:%M")), text_color=c.DANGER)
        elif not self.prov["keys"]:
            self.status.configure(text="sans clé", text_color=c.MUTED)
        else:
            self.status.configure(text=c.tr("{k} clé(s) • {m} modèle(s)", k=len(self.prov["keys"]), m=len(self.prov["models"])), text_color=c.SUCCESS)

    def toggle(self):
        self.prov["enabled"] = bool(self.sw.get())
        self.view.save()

    def expand(self):
        self.open = not self.open
        if self.open:
            self._build_body()
            self.body.pack(fill="x", padx=14, pady=(0, 12))
            self.btn.configure(text="Réduire ▴")
        else:
            self.body.pack_forget()
            self.btn.configure(text="Configurer ▾")

    # --------------------------------------------------------------- corps
    def _build_body(self):
        if getattr(self, "built", False):
            return
        self.built = True
        p = self.prov
        custom = p["kind"] == "custom"
        if custom:
            row = ctk.CTkFrame(self.body, fg_color="transparent")
            row.pack(fill="x", pady=2)
            self.name_e = c.entry(row, "Nom du fournisseur", 200)
            self.name_e.insert(0, p["name"])
            self.name_e.pack(side="left")
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=2)
        self.key_e = c.entry(row, "Clé(s) API — plusieurs clés séparées par « ; »", 420, show="•")
        self.key_e.insert(0, "; ".join(p["keys"]))
        self.key_e.pack(side="left")
        if p["kind"] in ai_cloud.PRESETS:
            c.ghost_btn(row, "Obtenir une clé gratuite", lambda: webbrowser.open(ai_cloud.PRESETS[p["kind"]]["key_url"]), width=210).pack(side="left", padx=8)
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=2)
        self.url_e = c.entry(row, "Adresse de l'API (compatible OpenAI)", 420)
        self.url_e.insert(0, p["base_url"])
        self.url_e.pack(side="left")
        bar = ctk.CTkFrame(self.body, fg_color="transparent")
        bar.pack(fill="x", pady=6)
        c.primary_btn(bar, "Récupérer les modèles gratuits", self.fetch, width=250).pack(side="left")
        c.ghost_btn(bar, "Choix automatique", self.auto, width=160).pack(side="left", padx=6)
        c.ghost_btn(bar, "Tester", self.test, width=100).pack(side="left")
        c.primary_btn(bar, "Enregistrer", self.save, width=130).pack(side="left", padx=6)
        if custom:
            c.ghost_btn(bar, "Supprimer", lambda: self.view.delete_provider(p["id"]), width=110, danger=True).pack(side="right")
        self.msg = c.label(self.body, "", size=12, wraplength=620)
        self.msg.pack(anchor="w")
        c.subtitle(self.body, "Cochez « Texte » pour la rédaction (l'ordre de la liste = ordre d'essai) et « OCR » pour la lecture de documents (modèles à vision).",
                   wraplength=620).pack(anchor="w", pady=(2, 4))
        self.list = ctk.CTkScrollableFrame(self.body, height=190, fg_color=c.SOFT)
        self.list.pack(fill="x")
        self.models = [{"id": m, "free": None, "vision": m in p["vision_models"], "context": 0}
                       for m in dict.fromkeys(p["models"] + p["vision_models"])]
        self.render_models()

    def render_models(self):
        for w in self.list.winfo_children():
            w.destroy()
        self.sel_text, self.sel_ocr = {}, {}
        chosen, chosen_v = set(self.prov["models"]), set(self.prov["vision_models"])
        if not self.models:
            c.subtitle(self.list, "Aucun modèle : cliquez sur « Récupérer les modèles gratuits ».").pack(anchor="w", padx=8, pady=8)
        for m in self.models:
            row = ctk.CTkFrame(self.list, fg_color="transparent")
            row.pack(fill="x", pady=1)
            vt = ctk.BooleanVar(value=m["id"] in chosen)
            ctk.CTkCheckBox(row, text="Texte", variable=vt, width=70, fg_color=c.ACCENT).pack(side="left", padx=(4, 0))
            self.sel_text[m["id"]] = vt
            if m["vision"] or m["id"] in chosen_v:
                vo = ctk.BooleanVar(value=m["id"] in chosen_v)
                ctk.CTkCheckBox(row, text="OCR", variable=vo, width=60, fg_color=c.ACCENT).pack(side="left", padx=(6, 0))
                self.sel_ocr[m["id"]] = vo
            tag = ("  🆓" if m["free"] else "") + (f"  ({m['context'] // 1000}k)" if m["context"] else "")
            c.label(row, m["id"] + tag, size=12).pack(side="left", padx=8)

    # ------------------------------------------------------------- actions
    def collect(self):
        p = self.prov
        p["keys"] = ai_cloud.split_keys(self.key_e.get()) if getattr(self, "built", False) else p["keys"]
        if getattr(self, "built", False):
            p["base_url"] = self.url_e.get().strip().rstrip("/")
            if p["kind"] == "custom":
                p["name"] = self.name_e.get().strip() or p["name"]
            p["models"] = [m["id"] for m in self.models if self.sel_text.get(m["id"]) and self.sel_text[m["id"]].get()]
            p["vision_models"] = [m["id"] for m in self.models if self.sel_ocr.get(m["id"]) and self.sel_ocr[m["id"]].get()]
        return p

    def note(self, text, ok=True):
        self.msg.configure(text=text, text_color=c.SUCCESS if ok else c.DANGER)

    def fetch(self):
        p = self.collect()
        if not p["base_url"]:
            return self.note(c.tr("Indiquez l'adresse de l'API."), False)
        key = (p["keys"] or [""])[0]
        self.note(c.tr("Récupération de la liste à jour..."))

        def done(ok, val):
            if not ok:
                return self.note(c.tr("Échec : {x}", x=str(val)[:200]), False)
            known = {m["id"] for m in val}
            keep = [m for m in self.models if m["id"] not in known and (m["id"] in p["models"] or m["id"] in p["vision_models"])]
            self.models = val + keep
            self.render_models()
            self.note(c.tr("{n} modèle(s) trouvé(s). Cochez ceux à utiliser puis enregistrez.", n=len(val)))

        c.run_bg(self, lambda: ai_cloud.fetch_models(p["kind"], p["base_url"], key), done)

    def auto(self):
        if not self.models:
            return self.note(c.tr("Récupérez d'abord la liste des modèles."), False)
        t, v = ai_cloud.auto_pick(self.models)
        for mid, var in self.sel_text.items():
            var.set(mid in t)
        for mid, var in self.sel_ocr.items():
            var.set(mid in v)
        self.note(c.tr("Sélection automatique faite : {n} modèle(s). Pensez à enregistrer.", n=len(t)))

    def save(self):
        self.collect()
        self.view.save()
        self.update_status()
        self.note(c.tr("Enregistré."))

    def test(self):
        p = dict(self.collect())
        p["enabled"] = True
        if not p["keys"] or not p["models"]:
            return self.note(c.tr("Ajoutez une clé et cochez au moins un modèle."), False)
        self.note(c.tr("Test en cours..."))
        msgs = ai_local._msgs(i18n.get_lang(), "Dis bonjour en une courte phrase.", "")

        def done(ok, val):
            ai_manager.persist_cooldowns(self.view.db)
            self.update_status()
            if not ok:
                reasons = " • ".join(val.reasons[:2]) if isinstance(val, ai_cloud.AIUnavailable) else str(val)[:160]
                return self.note(c.tr("Échec : {x}", x=reasons), False)
            self.note(f"✔ {val[1]} → {ai_local.clean_output(val[0])[:120]}")

        c.run_bg(self, lambda: ai_cloud.complete(p, msgs, None, 60), done)


class AiView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app, self.db = app, app.db
        self.cfg = ai_manager.load_config(self.db)
        ai_manager.load_cooldowns(self.db)
        self.cards = {}
        c.title(self, "Intelligence artificielle").pack(anchor="w")
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, pady=(10, 0))
        self._build_modes()
        self.order_box = c.card(self.body)
        self.order_box.pack(fill="x", pady=(0, 12))
        c.label(self.body, "Fournisseurs en ligne (paliers gratuits)", bold=True, size=16).pack(anchor="w", pady=(4, 6))
        self.prov_box = ctk.CTkFrame(self.body, fg_color="transparent")
        self.prov_box.pack(fill="x")
        self.render_providers()
        c.ghost_btn(self.body, "+  Ajouter un fournisseur personnalisé", self.add_provider, width=330).pack(anchor="w", pady=10)
        self.render_order()

    # ---------------------------------------------------------------- modes
    def _build_modes(self):
        card = c.card(self.body)
        card.pack(fill="x", pady=(0, 12))
        c.label(card, "Mode de fonctionnement", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 4))
        c.subtitle(card, "Vous décidez de ce qui est actif. L'IA rédige dans la langue de l'application, sauf demande contraire de l'utilisateur. "
                         "Si aucune IA n'est disponible (quota atteint, pas d'Internet), l'application utilise ses propres fonctions : "
                         "mise en forme automatique et OCR intégré.", wraplength=640).pack(anchor="w", padx=18)
        self.sw_local = ctk.CTkSwitch(card, text="IA locale (hors-ligne, modèle .gguf dans le dossier models)", progress_color=c.ACCENT, command=self.save_modes)
        self.sw_local.pack(anchor="w", padx=18, pady=(12, 4))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18)
        self.ai_model = ctk.CTkComboBox(row, values=["—"], width=280, height=36, state="readonly",
                                        command=lambda v: self.db.set_setting("ai_model", v))
        self.ai_model.pack(side="left")
        c.ghost_btn(row, "Ouvrir le dossier models", lambda: c.open_path(ai_local.primary_dir()), width=220).pack(side="left", padx=8)
        self.test_btn = c.ghost_btn(row, "Tester", self.test_local, width=100)
        self.test_btn.pack(side="left")
        self.local_status = c.label(card, "", size=12, wraplength=640)
        self.local_status.pack(anchor="w", padx=18, pady=(4, 8))
        self.sw_cloud = ctk.CTkSwitch(card, text="IA en ligne (clés gratuites, rotation automatique)", progress_color=c.ACCENT, command=self.save_modes)
        self.sw_cloud.pack(anchor="w", padx=18, pady=(6, 2))
        self.consent = ctk.CTkCheckBox(card, text="Je comprends que les textes envoyés à l'IA en ligne (et les pages scannées si l'OCR IA est activé) "
                                                  "quittent cet ordinateur et sont traités par le fournisseur choisi : à éviter pour les documents confidentiels.",
                                       fg_color=c.ACCENT, command=self.save_modes)
        self.consent.pack(anchor="w", padx=18, pady=(2, 6))
        self.sw_ocr = ctk.CTkSwitch(card, text="OCR IA : lire les documents scannés avec un modèle à vision (repli : OCR de l'application)",
                                    progress_color=c.ACCENT, command=self.save_modes)
        self.sw_ocr.pack(anchor="w", padx=18, pady=(2, 14))
        cfg = self.cfg
        for sw, key in ((self.sw_local, "local_enabled"), (self.sw_cloud, "cloud_enabled"), (self.sw_ocr, "ocr_enabled")):
            if cfg[key]:
                sw.select()
        if cfg["consent"]:
            self.consent.select()
        self.refresh_local()

    def refresh_local(self):
        models = [p.name for p, _ in ai_local.list_models()]
        self.ai_model.configure(values=models or ["—"])
        chosen = self.db.get_setting("ai_model", "")
        self.ai_model.set(chosen if chosen in models else (models[0] if models else "—"))
        ok, msg, _ = ai_local.status(self.ai_model.get())
        self.local_status.configure(text=c.tr("IA prête — modèle : {name}", name=msg) if ok else msg, text_color=c.SUCCESS if ok else c.MUTED)

    def test_local(self):
        ok, msg, path = ai_local.status(self.ai_model.get())
        if not ok:
            return c.error(msg, "IA locale")
        self.local_status.configure(text="Test en cours...", text_color=c.MUTED)
        prompt = ai_local.messages_free("Une phrase de politesse pour terminer un courrier.", i18n.get_lang())

        def done(ok2, val):
            if not ok2:
                self.refresh_local()
                return c.user_error(val, "Le test a échoué. Le modèle est peut-être incompatible ou trop lourd.")
            self.local_status.configure(text="✔ " + ai_local.clean_output(val)[:160], text_color=c.SUCCESS)

        c.run_bg(self, lambda: ai_local.generate(path, prompt, None, max_tokens=60), done)

    def save_modes(self):
        cfg = self.cfg
        cfg["local_enabled"] = bool(self.sw_local.get())
        cfg["cloud_enabled"] = bool(self.sw_cloud.get())
        cfg["consent"] = bool(self.consent.get())
        cfg["ocr_enabled"] = bool(self.sw_ocr.get())
        if (cfg["cloud_enabled"] or cfg["ocr_enabled"]) and not cfg["consent"]:
            cfg["cloud_enabled"] = cfg["ocr_enabled"] = False
            self.sw_cloud.deselect()
            self.sw_ocr.deselect()
            c.error("Cochez d'abord la case de confirmation : l'IA en ligne envoie vos textes au fournisseur.", "Confirmation requise")
        self.save()

    def save(self):
        ai_manager.save_config(self.db, self.cfg)
        self.render_order()

    # ---------------------------------------------------------- fournisseurs
    def render_providers(self):
        for w in self.prov_box.winfo_children():
            w.destroy()
        self.cards = {}
        for p in self.cfg["providers"]:
            card = ProviderCard(self.prov_box, self, p)
            card.pack(fill="x", pady=4)
            self.cards[p["id"]] = card

    def add_provider(self):
        n = 1
        ids = {p["id"] for p in self.cfg["providers"]}
        while f"custom-{n}" in ids:
            n += 1
        p = ai_manager.new_provider("custom", f"Personnalisé {n}", "", pid=f"custom-{n}")
        self.cfg["providers"].append(p)
        self.cfg["order"].append(p["id"])
        self.save()
        self.render_providers()
        self.cards[p["id"]].expand()

    def delete_provider(self, pid):
        if c.confirm("Supprimer ce fournisseur et ses clés ?"):
            self.cfg["providers"] = [p for p in self.cfg["providers"] if p["id"] != pid]
            self.cfg["order"] = [o for o in self.cfg["order"] if o != pid]
            self.save()
            self.render_providers()

    # ----------------------------------------------------------------- ordre
    def _entry_name(self, entry):
        if entry == "local":
            return c.tr("IA locale")
        return next((p["name"] for p in self.cfg["providers"] if p["id"] == entry), entry)

    def render_order(self):
        for w in self.order_box.winfo_children():
            w.destroy()
        c.label(self.order_box, "Ordre de priorité (le premier est essayé en premier)", bold=True, size=16).pack(anchor="w", padx=18, pady=(14, 6))
        order = self.cfg["order"]
        for i, entry in enumerate(order):
            row = ctk.CTkFrame(self.order_box, fg_color=c.SOFT, corner_radius=8)
            row.pack(fill="x", padx=14, pady=2)
            c.label(row, f"{i + 1}.", bold=True, width=28).pack(side="left", padx=(10, 0), pady=6)
            c.label(row, self._entry_name(entry), width=220).pack(side="left")
            on = self.cfg["local_enabled"] if entry == "local" else any(p["id"] == entry and p["enabled"] for p in self.cfg["providers"])
            c.label(row, "actif" if on else "désactivé", color=c.SUCCESS if on else c.MUTED, size=12).pack(side="left", padx=10)
            ctk.CTkButton(row, text="▼", width=32, fg_color="transparent", hover_color=c.CARD, text_color=c.TEXT,
                          command=lambda k=i: self.move(k, 1)).pack(side="right", padx=2)
            ctk.CTkButton(row, text="▲", width=32, fg_color="transparent", hover_color=c.CARD, text_color=c.TEXT,
                          command=lambda k=i: self.move(k, -1)).pack(side="right")
        bar = ctk.CTkFrame(self.order_box, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(8, 14))
        c.ghost_btn(bar, "Lever toutes les pauses", self.reset_pauses, width=220).pack(side="left")
        c.subtitle(bar, "Quand un quota est atteint, le fournisseur est mis en pause automatiquement puis repris.").pack(side="left", padx=12)

    def move(self, i, d):
        o = self.cfg["order"]
        j = i + d
        if 0 <= j < len(o):
            o[i], o[j] = o[j], o[i]
            self.save()

    def reset_pauses(self):
        ai_cloud.reset_cooldowns()
        ai_manager.persist_cooldowns(self.db)
        self.refresh()

    def refresh(self):
        self.refresh_local()
        for card in self.cards.values():
            card.update_status()
