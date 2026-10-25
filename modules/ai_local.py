"""IA locale hors-ligne : un petit modèle .gguf placé dans le dossier « models » rédige les textes.

Moteur : llama.cpp (paquet llama-cpp-python, embarqué dans l'exe). Aucune donnée ne quitte l'ordinateur.
L'IA ne rédige que le TEXTE ; la mise en page (en-tête, signature, typographie) reste faite par l'application.
"""
import os
import re
import sys
import threading
from pathlib import Path

from .paths import app_data_dir

SYSTEM = {
    "fr": "Tu es un secrétaire administratif expert. Tu écris en français, dans un style clair, courtois et professionnel. "
          "Tu réponds UNIQUEMENT avec le texte demandé : pas d'introduction, pas de commentaire, pas de titre, pas de markdown, "
          "pas d'astérisques. N'invente aucun chiffre, nom ou date qui ne figure pas dans les informations fournies. "
          "Langue par défaut : le français ; si la demande de l'utilisateur précise explicitement une autre langue, écris dans cette langue.",
    "es": "Eres un secretario administrativo experto. Escribes en español, con un estilo claro, cortés y profesional. "
          "Responde ÚNICAMENTE con el texto solicitado: sin introducción, sin comentarios, sin título, sin markdown, sin asteriscos. "
          "No inventes cifras, nombres ni fechas que no figuren en la información proporcionada. "
          "Idioma por defecto: español; si la petición del usuario indica expresamente otro idioma, escribe en ese idioma.",
    "en": "You are an expert administrative secretary. You write in English, in a clear, courteous and professional style. "
          "Reply ONLY with the requested text: no introduction, no commentary, no title, no markdown, no asterisks. "
          "Do not invent figures, names or dates that are not in the information provided. "
          "Default language: English; if the user's request explicitly asks for another language, write in that language.",
}

# champ de formulaire que l'IA sait rédiger, pour chaque document type : (clé du champ, consigne par langue)
AI_FIELDS = {
    "Lettre administrative": ("corps", {
        "fr": "Rédige le corps d'une lettre administrative (sans « Madame, Monsieur », sans formule de politesse finale, sans signature), en 2 à 4 paragraphes courts.",
        "es": "Redacta el cuerpo de una carta administrativa (sin saludo inicial, sin fórmula de despedida, sin firma), en 2 a 4 párrafos cortos.",
        "en": "Write the body of an administrative letter (no salutation, no closing phrase, no signature), in 2 to 4 short paragraphs."}),
    "Note de service": ("corps", {
        "fr": "Rédige le texte d'une note de service interne, claire et directive, en 1 à 3 paragraphes.",
        "es": "Redacta el texto de una nota interna, clara y directiva, en 1 a 3 párrafos.",
        "en": "Write the text of an internal memo, clear and directive, in 1 to 3 paragraphs."}),
    "Attestation (libre)": ("corps", {
        "fr": "Rédige le texte d'une attestation officielle, à la première personne (« Je soussigné(e)... »), sans date ni signature.",
        "es": "Redacta el texto de un certificado oficial, en primera persona (« Quien suscribe... »), sin fecha ni firma.",
        "en": "Write the text of an official certificate, in the first person (\"I, the undersigned...\"), without date or signature."}),
    "Procès-verbal de réunion": ("contenu", {
        "fr": "À partir des notes fournies, rédige le déroulement et les décisions d'un procès-verbal de réunion, en paragraphes courts au passé.",
        "es": "A partir de las notas proporcionadas, redacta el desarrollo y las decisiones de un acta de reunión, en párrafos cortos en pasado.",
        "en": "From the notes provided, write the proceedings and decisions of meeting minutes, in short paragraphs in the past tense."}),
    "Convocation": ("ordre", {
        "fr": "Propose l'ordre du jour de cette réunion : un point par ligne, sans numérotation ni puces, 3 à 6 points.",
        "es": "Propón el orden del día de esta reunión: un punto por línea, sin numeración ni viñetas, de 3 a 6 puntos.",
        "en": "Propose the agenda of this meeting: one item per line, no numbering or bullets, 3 to 6 items."}),
    "Procuration": ("objet", {
        "fr": "Complète la phrase « ...afin de » : décris en une phrase précise l'objet de la procuration (sans point final inutile).",
        "es": "Completa la frase «...para»: describe en una frase precisa el objeto del poder.",
        "en": "Complete the phrase \"...in order to\": describe in one precise sentence the purpose of the power of attorney."}),
    "Décharge": ("objet", {
        "fr": "Décris en une phrase précise l'objet remis (documents, matériel, somme...) à partir des informations fournies.",
        "es": "Describe en una frase precisa el objeto entregado (documentos, material, importe...) a partir de la información proporcionada.",
        "en": "Describe in one precise sentence the item handed over (documents, equipment, sum...) from the information provided."}),
}
IMPROVE = {
    "fr": "Corrige l'orthographe, la grammaire et la ponctuation du texte suivant et améliore légèrement le style, sans changer le sens ni ajouter d'informations. Conserve les paragraphes.",
    "es": "Corrige la ortografía, la gramática y la puntuación del siguiente texto y mejora ligeramente el estilo, sin cambiar el sentido ni añadir información. Conserva los párrafos.",
    "en": "Correct the spelling, grammar and punctuation of the following text and slightly improve the style, without changing the meaning or adding information. Keep the paragraphs.",
}
FREE = {
    "fr": "Rédige le texte demandé ci-dessous, prêt à être utilisé (paragraphes courts, ton professionnel).",
    "es": "Redacta el texto solicitado a continuación, listo para usar (párrafos cortos, tono profesional).",
    "en": "Write the text requested below, ready to use (short paragraphs, professional tone).",
}
LABELS = {  # libellés des champs envoyés comme contexte
    "fr": {"destinataire": "Destinataire", "fonction": "Fonction du destinataire", "objet": "Objet", "expediteur": "Expéditeur",
           "lieu": "Lieu", "jour": "Jour", "heure": "Heure", "participants": "Participants", "de": "De", "a": "À",
           "mandataire": "Mandataire", "signataire": "Signataire", "titre": "Titre", "adresse": "Adresse", "destinataires": "Destinataires"},
    "es": {"destinataire": "Destinatario", "fonction": "Cargo del destinatario", "objet": "Asunto", "expediteur": "Remitente",
           "lieu": "Lugar", "jour": "Día", "heure": "Hora", "participants": "Participantes", "de": "De", "a": "Para",
           "mandataire": "Apoderado", "signataire": "Firmante", "titre": "Título", "adresse": "Dirección", "destinataires": "Destinatarios"},
    "en": {"destinataire": "Recipient", "fonction": "Recipient's position", "objet": "Subject", "expediteur": "Sender",
           "lieu": "Place", "jour": "Day", "heure": "Time", "participants": "Attendees", "de": "From", "a": "To",
           "mandataire": "Attorney", "signataire": "Signatory", "titre": "Title", "adresse": "Address", "destinataires": "Recipients"},
}
NOTES = {"fr": "Informations / points à intégrer", "es": "Información / puntos a incluir", "en": "Information / points to include"}


# ------------------------------------------------------------------ modèles
def models_dirs():
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    return [base / "models", app_data_dir() / "models"]


def primary_dir() -> Path:
    for d in models_dirs():
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".w"
            probe.write_text("x")
            probe.unlink()
            return d
        except OSError:
            continue
    return models_dirs()[-1]


def list_models():
    out = []
    for d in models_dirs():
        if d.is_dir():
            out += [(f, f.stat().st_size / 1e9) for f in sorted(d.glob("*.gguf"))]
    return out


def engine_available() -> bool:
    try:
        import llama_cpp  # noqa: F401
        return True
    except Exception:
        return False


def status(selected: str = ""):
    """(prêt ?, message clair pour l'utilisateur, chemin du modèle ou None)."""
    if not engine_available():
        return False, "Le moteur d'IA n'est pas inclus dans cette version de l'application.", None
    models = list_models()
    if not models:
        return False, "Aucun modèle trouvé : placez un fichier .gguf dans le dossier models.", None
    pick = next((p for p, _ in models if p.name == selected), models[0][0])
    return True, pick.name, pick


# ------------------------------------------------------------------ moteur
class _Engine:
    llm, path, lock = None, None, threading.Lock()


def _load(path: Path):
    if _Engine.llm is not None and _Engine.path == path:
        return _Engine.llm
    from llama_cpp import Llama
    _Engine.llm = None
    threads = max(2, (os.cpu_count() or 4) - 1)
    _Engine.llm = Llama(model_path=str(path), n_ctx=3072, n_threads=threads, n_gpu_layers=0, verbose=False)
    _Engine.path = path
    return _Engine.llm


def generate(path: Path, messages, on_token=None, max_tokens=700, temperature=0.4) -> str:
    """Génère le texte ; appelle on_token(morceau) au fil de l'eau (à exécuter dans un thread)."""
    with _Engine.lock:
        llm = _load(path)
        parts = []
        for chunk in llm.create_chat_completion(messages=messages, max_tokens=max_tokens, temperature=temperature,
                                                top_p=0.9, repeat_penalty=1.1, stream=True):
            piece = chunk["choices"][0].get("delta", {}).get("content") or ""
            if piece:
                parts.append(piece)
                if on_token:
                    on_token(piece)
        return "".join(parts)


# ------------------------------------------------------------------ prompts
def _msgs(lang, instruction, content):
    lang = lang if lang in SYSTEM else "fr"
    return [{"role": "system", "content": SYSTEM[lang]}, {"role": "user", "content": f"{instruction}\n\n{content}"}]


def messages_for_doc(doc_type, values, lang="fr"):
    """Consigne pour rédiger le champ « IA » d'un document type à partir des autres champs du formulaire."""
    key, instr = AI_FIELDS[doc_type]
    lang = lang if lang in SYSTEM else "fr"
    lab = LABELS[lang]
    ctx = [f"{lab.get(k, k)} : {v}" for k, v in values.items() if k != key and v.strip() and k in lab]
    notes = values.get(key, "").strip()
    content = "\n".join(ctx) + (f"\n{NOTES[lang]} :\n{notes}" if notes else "")
    return key, _msgs(lang, instr[lang], content.strip() or "—")


def messages_improve(text, lang="fr"):
    return _msgs(lang, IMPROVE.get(lang, IMPROVE["fr"]), text)


def messages_free(request, lang="fr"):
    return _msgs(lang, FREE.get(lang, FREE["fr"]), request)


_CHATTER = re.compile(r"^(voici|bien sûr|certainement|d'accord|sure|here is|here's|of course|claro|aquí está|por supuesto)\b.*:\s*$", re.I)


def clean_output(text: str) -> str:
    t = re.sub(r"<think>.*?(</think>|$)", "", text, flags=re.S).replace("\r", "").strip()
    t = re.sub(r"\*\*|__|`|^#{1,6}\s*", "", t, flags=re.M)
    lines = [l.rstrip() for l in t.split("\n")]
    while lines and (not lines[0].strip() or _CHATTER.match(lines[0].strip())):
        lines.pop(0)
    t = "\n".join(lines).strip()
    if len(t) > 1 and t[0] in "\"«“" and t[-1] in "\"»”":
        t = t[1:-1].strip()
    return re.sub(r"\n{3,}", "\n\n", t)
