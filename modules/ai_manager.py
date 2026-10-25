"""Orchestration de l'IA : IA locale + fournisseurs en ligne (clés gratuites), ordre de priorité et repli.

Règles : l'administrateur active ce qu'il veut ; l'ordre est respecté ; en cas de quota, le fournisseur est mis en
pause et on passe au suivant ; si plus rien n'est disponible, l'application utilise ses propres fonctions
(mise en forme automatique, OCR intégré).
"""
import copy
import json
import re

from . import ai_cloud, ai_local, i18n, security
from .ai_cloud import AIUnavailable

DEFAULT_CFG = {"local_enabled": False, "cloud_enabled": False, "consent": False, "ocr_enabled": False,
               "order": ["local"], "providers": []}
OCR_SYSTEM = ("You are a precise OCR engine. Transcribe exactly the text visible in the image, in its ORIGINAL language "
              "(never translate). Keep the reading order, paragraphs and lists. Render tables as Markdown tables. "
              "Output only the transcription, with no comment.")
OCR_INSTRUCTION = "Transcribe this document page."


def new_provider(kind: str, name: str = "", base_url: str = "", pid: str | None = None):
    p = ai_cloud.PRESETS.get(kind, {})
    return {"id": pid or kind, "kind": kind, "name": name or p.get("name", kind), "base_url": base_url or p.get("base", ""),
            "keys": [], "models": list(p.get("models", [])), "vision_models": list(p.get("vision", [])), "enabled": False}


def load_config(db) -> dict:
    token = db.get_setting("ai_cfg", "")
    raw = security.decrypt_secret(token) if token else None
    try:
        cfg = json.loads(raw) if raw else {}
    except ValueError:
        cfg = {}
    for k, v in DEFAULT_CFG.items():
        cfg.setdefault(k, copy.deepcopy(v))
    have = {p["id"] for p in cfg["providers"]}
    for kind in ai_cloud.PRESETS:
        if kind not in have:
            cfg["providers"].append(new_provider(kind))
    ids = ["local"] + [p["id"] for p in cfg["providers"]]
    cfg["order"] = [o for o in cfg["order"] if o in ids] + [i for i in ids if i not in cfg["order"]]
    return cfg


def save_config(db, cfg: dict):
    db.set_setting("ai_cfg", security.encrypt_secret(json.dumps(cfg)))


def load_cooldowns(db):
    try:
        ai_cloud.import_cooldowns(json.loads(db.get_setting("ai_cooldowns", "{}")))
    except ValueError:
        ai_cloud.import_cooldowns({})


def persist_cooldowns(db):
    db.set_setting("ai_cooldowns", json.dumps(ai_cloud.export_cooldowns()))


def snapshot(db) -> dict:
    """Copie de la configuration à transmettre au thread de travail (SQLite reste dans le thread principal)."""
    cfg = load_config(db)
    ok, _msg, path = ai_local.status(db.get_setting("ai_model", ""))
    return {"cfg": cfg, "local_path": path if ok else None}


def cloud_ready(snap) -> bool:
    c = snap["cfg"]
    return bool(c["cloud_enabled"] and c["consent"] and any(p["enabled"] and p["keys"] and p["models"] for p in c["providers"]))


def local_ready(snap) -> bool:
    return bool(snap["cfg"]["local_enabled"] and snap["local_path"])


def enabled(snap) -> bool:
    return local_ready(snap) or cloud_ready(snap)


def ocr_ready(snap) -> bool:
    c = snap["cfg"]
    return bool(c["ocr_enabled"] and c["cloud_enabled"] and c["consent"]
                and any(p["enabled"] and p["keys"] and p["vision_models"] for p in c["providers"]))


def run(snap, messages, on_token=None, max_tokens=700, temperature=0.4, vision=False):
    """Retourne (texte, étiquette de la source). Lève AIUnavailable avec les raisons si tout échoue."""
    cfg, reasons = snap["cfg"], []
    for entry in cfg["order"]:
        if entry == "local":
            if vision or not local_ready(snap):
                continue
            try:
                return ai_local.generate(snap["local_path"], messages, on_token, max_tokens, temperature), "IA locale"
            except Exception as e:  # noqa: BLE001
                reasons.append(f"IA locale : {type(e).__name__}")
                if on_token:
                    on_token(None)
            continue
        if not (cfg["cloud_enabled"] and cfg["consent"]):
            continue
        prov = next((p for p in cfg["providers"] if p["id"] == entry and p["enabled"]), None)
        if not prov:
            continue
        try:
            return ai_cloud.complete(prov, messages, on_token, max_tokens, temperature, vision)
        except AIUnavailable as e:
            reasons += e.reasons
    raise AIUnavailable(reasons or ["Aucune IA activée"])


def ocr_page(snap, jpeg: bytes):
    msgs = ai_cloud.vision_messages(jpeg, OCR_INSTRUCTION, OCR_SYSTEM)
    text, label = run(snap, msgs, None, max_tokens=3000, temperature=0.0, vision=True)
    return strip_thinking(text), label


def strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()


def short_reasons(exc: AIUnavailable, n=3) -> str:
    return " • ".join(exc.reasons[:n]) if exc.reasons else i18n.t("Aucune IA activée")
