"""IA en ligne (paliers gratuits) : fournisseurs compatibles OpenAI, rotation automatique et pauses (cooldown).

Fournisseurs prédéfinis : OpenRouter, Groq, Google Gemini, Mistral, DeepSeek, BazaarLink + fournisseur personnalisé
(toute API « compatible OpenAI »). Aucune bibliothèque externe : urllib uniquement.
Les clés ne sont jamais écrites dans les journaux.
"""
import base64
import hashlib
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PRESETS = {
    "openrouter": {"name": "OpenRouter", "base": "https://openrouter.ai/api/v1", "key_url": "https://openrouter.ai/keys",
                   "models": [], "vision": []},
    "bazaarlink": {"name": "BazaarLink", "base": "https://bazaarlink.ai/api/v1", "key_url": "https://bazaarlink.ai/free",
                   "models": ["auto:free"], "vision": []},
    "groq": {"name": "Groq", "base": "https://api.groq.com/openai/v1", "key_url": "https://console.groq.com/keys",
             "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"], "vision": []},
    "gemini": {"name": "Google Gemini", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
               "key_url": "https://aistudio.google.com/apikey", "models": ["gemini-2.5-flash"], "vision": ["gemini-2.5-flash"]},
    "mistral": {"name": "Mistral", "base": "https://api.mistral.ai/v1", "key_url": "https://console.mistral.ai/api-keys",
                "models": ["mistral-small-latest"], "vision": []},
    "deepseek": {"name": "DeepSeek", "base": "https://api.deepseek.com/v1", "key_url": "https://platform.deepseek.com/api_keys",
                 "models": ["deepseek-chat"], "vision": []},
}
_NOT_CHAT = ("embed", "whisper", "tts", "guard", "moderat", "rerank", "imagen", "veo", "dall", "image-gen", "audio", "speech",
             "transcri", "orpheus", "playai", "aqa", "ocr-")
_VISION_HINT = ("vision", "-vl", "vl-", "pixtral", "scout", "maverick", "gemini", "gpt-4o", "llava", "gemma-3", "gemma-4", "omni")
DEFAULT_COOLDOWN = 65          # secondes (limite par minute)
TIMEOUT_CONNECT = 25
TIMEOUT_STREAM = 120

_lock = threading.Lock()
COOL: dict = {}                # portée -> {"until": ts, "reason": str}
_RR: dict = {}                 # rotation des clés par fournisseur


class AIError(Exception):
    def __init__(self, kind, message, retry_after=None):
        super().__init__(message)
        self.kind, self.retry_after = kind, retry_after


class AIUnavailable(Exception):
    """Aucun fournisseur n'a pu répondre (quotas, clés absentes, réseau...)."""

    def __init__(self, reasons):
        super().__init__("; ".join(reasons[-4:]) or "aucun fournisseur disponible")
        self.reasons = reasons


def key_id(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:10]


def split_keys(text: str):
    return [k.strip() for k in re.split(r"[;,\s]+", text or "") if k.strip()]


# ------------------------------------------------------------------ pauses
def _midnight_utc():
    now = datetime.now(timezone.utc)
    return (now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() + 86400) + 30


def set_cooldown(scope: str, seconds: float, reason: str):
    with _lock:
        COOL[scope] = {"until": time.time() + max(5.0, seconds), "reason": reason}


def clear_cooldown(scope: str):
    with _lock:
        COOL.pop(scope, None)


def cooling(scope: str):
    with _lock:
        e = COOL.get(scope)
        if e and e["until"] > time.time():
            return e
        COOL.pop(scope, None)
        return None


def export_cooldowns():
    with _lock:
        return {k: v for k, v in COOL.items() if v["until"] > time.time()}


def import_cooldowns(data):
    with _lock:
        COOL.clear()
        for k, v in (data or {}).items():
            if isinstance(v, dict) and v.get("until", 0) > time.time():
                COOL[k] = {"until": float(v["until"]), "reason": str(v.get("reason", ""))}


def reset_cooldowns():
    with _lock:
        COOL.clear()


def next_available(prov_id: str):
    """Heure (timestamp) de la plus proche reprise pour ce fournisseur, ou None."""
    with _lock:
        ts = [v["until"] for k, v in COOL.items() if k.startswith(prov_id + ":") and v["until"] > time.time()]
    return min(ts) if ts else None


# ------------------------------------------------------------------ HTTP
def _retry_after(headers, body: str):
    ra = headers.get("Retry-After") if headers else None
    if ra:
        try:
            return float(ra)
        except ValueError:
            try:
                from email.utils import parsedate_to_datetime
                return max(1.0, parsedate_to_datetime(ra).timestamp() - time.time())
            except Exception:
                pass
    reset = headers.get("X-RateLimit-Reset") if headers else None          # OpenRouter : époch en ms
    if reset:
        try:
            v = float(reset)
            v = v / 1000 if v > 1e11 else v
            return max(1.0, v - time.time())
        except ValueError:
            pass
    m = re.search(r'retryDelay"?\s*:\s*"?([0-9.]+)s', body)
    if m:
        return float(m.group(1)) + 1
    m = re.search(r"(?:try again|retry) in (?:(\d+)m)?\s*([0-9.]+)s", body, re.I)
    if m:
        return float(m.group(1) or 0) * 60 + float(m.group(2)) + 1
    return None


def classify(code: int, body: str, headers=None) -> AIError:
    low = body.lower()
    snippet = re.sub(r"\s+", " ", body)[:160]
    if code in (401, 403):
        return AIError("auth", f"clé refusée ({code})")
    if code == 402:
        return AIError("payment", "crédits insuffisants (402)")
    if code == 429 or any(w in low for w in ("rate limit", "quota", "resource_exhausted", "too many requests")) and code in (400, 403, 503):
        ra = _retry_after(headers, body)
        daily = any(w in low for w in ("per day", "daily", "rpd", "tpd", "perday", "free-models-per-day", "requests per day"))
        if daily and (ra is None or ra < 3600):
            ra = _midnight_utc() - time.time()
        return AIError("quota", f"quota atteint ({snippet})", ra or DEFAULT_COOLDOWN)
    if code in (404, 400, 422):
        return AIError("model", f"modèle ou requête refusé ({code}) {snippet}")
    if code >= 500 or code in (408, 409):
        return AIError("transient", f"service indisponible ({code})")
    return AIError("other", f"erreur {code} {snippet}")


def _open(method, url, key, body=None, timeout=TIMEOUT_CONNECT):
    headers = {"Accept": "application/json", "User-Agent": "SecretariatPro/1.2"}
    if key:
        headers["Authorization"] = "Bearer " + key
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if "openrouter" in url or "bazaarlink" in url:
        headers["X-Title"] = "SecretariatPro"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        try:
            text = e.read(4000).decode("utf-8", "replace")
        except Exception:
            text = ""
        raise classify(e.code, text, e.headers)
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
        raise AIError("transient", f"réseau indisponible ({type(e).__name__})")


# ------------------------------------------------------------------ modèles
def _is_chat(mid: str) -> bool:
    low = mid.lower()
    return not any(w in low for w in _NOT_CHAT)


def fetch_models(kind: str, base: str, key: str = ""):
    """Liste des modèles du fournisseur (à jour). Retourne [{'id','free','vision','context'}] triés (gratuits d'abord)."""
    with _open("GET", base.rstrip("/") + "/models", key) as r:
        payload = json.loads(r.read().decode("utf-8", "replace"))
    items = payload.get("data") if isinstance(payload, dict) else payload
    out = []
    for m in items or []:
        mid = str(m.get("id") or m.get("name") or "")
        mid = mid[7:] if mid.startswith("models/") else mid
        if not mid or not _is_chat(mid):
            continue
        arch = m.get("architecture") or {}
        pricing = m.get("pricing") or {}
        free = None
        if pricing:
            try:
                free = float(pricing.get("prompt", 1)) == 0 and float(pricing.get("completion", 1)) == 0
            except (TypeError, ValueError):
                free = None
        if mid.endswith(":free") or mid.startswith("auto:free"):
            free = True
        outs = arch.get("output_modalities")
        if outs and "text" not in outs:
            continue
        ins = arch.get("input_modalities")
        vision = ("image" in ins) if ins else any(h in mid.lower() for h in _VISION_HINT)
        ctx = m.get("context_length") or m.get("context_window") or (m.get("top_provider") or {}).get("context_length") or 0
        out.append({"id": mid, "free": free, "vision": bool(vision), "context": int(ctx or 0)})
    only_free = [m for m in out if m["free"]]
    if kind in ("openrouter", "bazaarlink") and only_free:           # ces deux-là mélangent gratuit et payant
        out = only_free
    out.sort(key=lambda m: (not m["free"], -m["context"], m["id"]))
    return out


def auto_pick(models, n=6):
    """Sélection automatique : modèles gratuits (ou du palier du fournisseur) avec le plus grand contexte."""
    pool = [m for m in models if m["free"] is not False]
    return [m["id"] for m in pool[:n]], [m["id"] for m in pool if m["vision"]][:3]


# ------------------------------------------------------------------ discussion
def _stream_chat(base, key, model, messages, on_token, max_tokens, temperature):
    body = {"model": model, "messages": messages, "stream": True, "max_tokens": max_tokens, "temperature": temperature}
    parts = []
    with _open("POST", base.rstrip("/") + "/chat/completions", key, body, TIMEOUT_STREAM) as r:
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "event-stream" not in ctype:                                   # le serveur a ignoré « stream »
            obj = json.loads(r.read().decode("utf-8", "replace"))
            if obj.get("error"):
                raise _inline_error(obj["error"])
            text = ((obj.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            if text and on_token:
                on_token(text)
            return text
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                obj = json.loads(payload)
            except ValueError:
                continue
            if obj.get("error"):
                raise _inline_error(obj["error"])
            for ch in obj.get("choices") or []:
                piece = (ch.get("delta") or {}).get("content")
                if piece:
                    parts.append(piece)
                    if on_token:
                        on_token(piece)
    return "".join(parts)


def _inline_error(err):
    code = err.get("code") if isinstance(err, dict) else None
    msg = json.dumps(err)[:300] if isinstance(err, dict) else str(err)
    try:
        return classify(int(code), msg)
    except (TypeError, ValueError):
        return classify(500, msg)


def _scopes(prov_id, key, model):
    return f"{prov_id}:{key_id(key)}", f"{prov_id}:{key_id(key)}:{model}"


def _penalize(prov_id, key, model, err: AIError):
    key_scope, model_scope = _scopes(prov_id, key, model)
    if err.kind == "auth":
        set_cooldown(key_scope, 12 * 3600, "clé refusée")
    elif err.kind == "quota":
        set_cooldown(model_scope, err.retry_after or DEFAULT_COOLDOWN, "quota atteint")
    elif err.kind == "payment":
        set_cooldown(model_scope, 6 * 3600, "crédits insuffisants")
    elif err.kind == "model":
        set_cooldown(model_scope, 24 * 3600, "modèle indisponible")
    else:
        set_cooldown(model_scope, 45, "service indisponible")


def candidates(provider, vision=False):
    """(clé, modèle) disponibles pour ce fournisseur, en alternant les clés (rotation)."""
    keys = [k for k in provider.get("keys", []) if k]
    models = provider.get("vision_models" if vision else "models", [])
    if not keys or not models:
        return []
    pid = provider["id"]
    start = _RR.get(pid, 0) % len(keys)
    ordered = keys[start:] + keys[:start]
    out = []
    for model in models:
        for key in ordered:
            ks, ms = _scopes(pid, key, model)
            if not cooling(ks) and not cooling(ms):
                out.append((key, model))
    return out


def complete(provider, messages, on_token=None, max_tokens=700, temperature=0.4, vision=False, max_attempts=8):
    """Essaie les couples (clé, modèle) d'UN fournisseur ; retourne (texte, étiquette). Lève AIUnavailable."""
    reasons, attempts = [], 0
    pid, name = provider["id"], provider["name"]
    if not provider.get("keys"):
        raise AIUnavailable([f"{name} : aucune clé"])
    for key, model in candidates(provider, vision):
        if attempts >= max_attempts:
            break
        attempts += 1
        try:
            text = _stream_chat(provider["base_url"], key, model, messages, on_token, max_tokens, temperature)
            if not text.strip():
                raise AIError("transient", "réponse vide")
            clear_cooldown(_scopes(pid, key, model)[1])
            _RR[pid] = _RR.get(pid, 0) + 1
            return text, f"{name} · {model}"
        except AIError as e:
            _penalize(pid, key, model, e)
            reasons.append(f"{name}/{model} : {e}")
            if on_token:
                on_token(None)                    # l'interface efface le début de texte déjà affiché
    if not reasons:
        nxt = next_available(pid)
        when = datetime.fromtimestamp(nxt).strftime("%H:%M") if nxt else "?"
        reasons.append(f"{name} : en pause (reprise vers {when})")
    raise AIUnavailable(reasons)


def vision_messages(image_jpeg: bytes, instruction: str, system: str):
    b64 = base64.b64encode(image_jpeg).decode()
    return [{"role": "system", "content": system},
            {"role": "user", "content": [{"type": "text", "text": instruction},
                                         {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]
