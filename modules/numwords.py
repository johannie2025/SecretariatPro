"""Nombres et montants en toutes lettres (français)."""
from decimal import Decimal, ROUND_HALF_UP

_U = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze",
      "douze", "treize", "quatorze", "quinze", "seize"]
_T = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _b100(n, final):
    if n < 17:
        return _U[n]
    if n < 20:
        return "dix-" + _U[n - 10]
    if n < 70:
        t, u = divmod(n, 10)
        return _T[t] if u == 0 else _T[t] + (" et un" if u == 1 else "-" + _U[u])
    if n < 80:
        return "soixante et onze" if n == 71 else "soixante-" + _b100(n - 60, final)
    if n == 80:
        return "quatre-vingts" if final else "quatre-vingt"
    return "quatre-vingt-" + _b100(n - 80, final)


def _b1000(n, final):
    h, r = divmod(n, 100)
    if h == 0:
        return _b100(r, final)
    head = "cent" if h == 1 else _U[h] + " cent"
    if r == 0:
        return head + ("s" if h > 1 and final else "")
    return head + " " + _b100(r, final)


def _fr(n: int) -> str:
    if n < 0 or n >= 10 ** 12:
        raise ValueError("Nombre hors limites.")
    if n == 0:
        return "zéro"
    parts = []
    for value, sing, plur in ((10 ** 9, "milliard", "milliards"), (10 ** 6, "million", "millions")):
        q, n = divmod(n, value)
        if q:
            parts.append(f"{_b1000(q, True)} {sing if q == 1 else plur}")
    q, n = divmod(n, 1000)
    if q:
        parts.append("mille" if q == 1 else f"{_b1000(q, False)} mille")
    if n:
        parts.append(_b1000(n, True))
    return " ".join(parts)


# ------------------------------------------------------------------ espagnol
_ES_U = ["cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez", "once", "doce",
         "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno",
         "veintidós", "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
_ES_T = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
_ES_H = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
         7: "setecientos", 8: "ochocientos", 9: "novecientos"}


def _es100(n):
    if n < 30:
        return _ES_U[n]
    t, u = divmod(n, 10)
    return _ES_T[t] + (" y " + _ES_U[u] if u else "")


def _es1000(n):
    if n == 100:
        return "cien"
    h, r = divmod(n, 100)
    head = _ES_H.get(h, "")
    return (head + " " + _es100(r)).strip() if r else head


def _apo(s):
    """uno → un (devant un nom ou mil/millón)."""
    if s.endswith("veintiuno"):
        return s[:-9] + "veintiún"
    return s[:-3] + "un" if s.endswith("uno") else s


def _es(n: int) -> str:
    if n < 0 or n >= 10 ** 12:
        raise ValueError("Nombre hors limites.")
    if n == 0:
        return "cero"
    parts = []
    q, n = divmod(n, 10 ** 9)
    if q:
        parts.append("mil millones" if q == 1 else _apo(_es_group(q)) + " mil millones")
    q, n = divmod(n, 10 ** 6)
    if q:
        parts.append("un millón" if q == 1 else _apo(_es_group(q)) + " millones")
    q, n = divmod(n, 1000)
    if q:
        parts.append("mil" if q == 1 else _apo(_es1000(q)) + " mil")
    if n:
        parts.append(_es1000(n))
    return " ".join(parts)


def _es_group(q):
    return _es1000(q) if q < 1000 else _es(q)


# -------------------------------------------------------------------- anglais
_EN_U = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_EN_T = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}


def _en100(n):
    if n < 20:
        return _EN_U[n]
    t, u = divmod(n, 10)
    return _EN_T[t] + ("-" + _EN_U[u] if u else "")


def _en1000(n):
    h, r = divmod(n, 100)
    out = []
    if h:
        out.append(_EN_U[h] + " hundred")
    if r:
        out.append(_en100(r))
    return " ".join(out)


def _en(n: int) -> str:
    if n < 0 or n >= 10 ** 12:
        raise ValueError("Nombre hors limites.")
    if n == 0:
        return "zero"
    parts = []
    for value, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        q, n = divmod(n, value)
        if q:
            parts.append(f"{_en1000(q)} {name}")
    if n:
        parts.append(_en1000(n))
    return " ".join(parts)


def number_to_words(n: int, lang: str = "fr") -> str:
    return {"fr": _fr, "es": _es, "en": _en}.get(lang, _fr)(n)


_CUR = {
    "fr": {"FCFA": ("franc CFA", "francs CFA"), "EUR": ("euro", "euros"), "USD": ("dollar", "dollars")},
    "es": {"FCFA": ("franco CFA", "francos CFA"), "EUR": ("euro", "euros"), "USD": ("dólar", "dólares")},
    "en": {"FCFA": ("CFA franc", "CFA francs"), "EUR": ("euro", "euros"), "USD": ("dollar", "dollars")},
}
_CENT = {"fr": ("centime", "centimes", " et "), "es": ("céntimo", "céntimos", " con "), "en": ("cent", "cents", " and ")}
_CFA = ("FCFA", "XAF", "XOF")


def amount_in_words(value, currency="FCFA", lang="fr") -> str:
    lang = lang if lang in _CUR else "fr"
    v = Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    whole, cents = int(v), int((v - int(v)) * 100)
    if currency in _CFA:                              # pas de centimes en zone CFA
        whole, cents = int(v.quantize(Decimal("1"), ROUND_HALF_UP)), 0
    key = "FCFA" if currency in _CFA else currency
    s, p = _CUR[lang].get(key, (currency, currency))
    words = number_to_words(whole, lang)
    if lang == "es":
        words = _apo(words)                           # veintiún francos, treinta y un euros
    text = f"{words} {s if whole == 1 else p}"
    if key in ("EUR", "USD") and cents:
        cs, cp, joiner = _CENT[lang]
        cw = _apo(number_to_words(cents, lang)) if lang == "es" else number_to_words(cents, lang)
        text += f"{joiner}{cw} {cs if cents == 1 else cp}"
    return text[0].upper() + text[1:]
