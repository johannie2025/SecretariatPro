"""OCR 100 % local (RapidOCR / ONNX) pour images et PDF (scannés ou vectoriels)."""
import re
from pathlib import Path

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
MAX_BYTES = 60 * 1024 * 1024
MAX_PAGES = 100
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def _lines_from_result(result):
    """Regroupe les boîtes détectées en lignes lisibles (haut→bas, gauche→droite)."""
    items = []
    for box, text, _score in result or []:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append((sum(ys) / 4, max(ys) - min(ys), min(xs), text))
    items.sort(key=lambda i: (i[0], i[2]))
    lines, cur, cur_y, cur_h = [], [], None, 1
    for cy, h, x, text in items:
        if cur and abs(cy - cur_y) > 0.6 * max(cur_h, h):
            lines.append(" ".join(t for _, t in sorted(cur)))
            cur = []
        if not cur:
            cur_y, cur_h = cy, h
        cur.append((x, text))
    if cur:
        lines.append(" ".join(t for _, t in sorted(cur)))
    return lines


def _ocr_array(arr):
    result, _ = _get_engine()(arr)
    return "\n".join(_lines_from_result(result))


def clean_text(text: str) -> str:
    text = text.replace("\r", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)       # mots coupés en fin de ligne
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(l.strip() for l in text.split("\n")).strip()


def extract_text(path: str, progress=None) -> str:
    import numpy as np
    p = Path(path)
    if not p.is_file():
        raise ValueError("Fichier introuvable.")
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("Fichier trop volumineux (60 Mo maximum).")
    ext = p.suffix.lower()
    if ext in IMAGE_EXT:
        from PIL import Image
        with Image.open(p) as im:
            arr = np.ascontiguousarray(np.array(im.convert("RGB"))[:, :, ::-1])
        return clean_text(_ocr_array(arr))
    if ext == ".pdf":
        try:
            import pymupdf as fitz
        except ImportError:  # anciennes versions
            import fitz
        out = []
        with fitz.open(p) as pdf:
            total = min(len(pdf), MAX_PAGES)
            for i in range(total):
                page = pdf[i]
                txt = page.get_text().strip()
                if len(txt) < 30:                         # page scannée → OCR
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
                    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                    txt = _ocr_array(np.ascontiguousarray(arr[:, :, ::-1]))
                out.append(txt)
                if progress:
                    progress(i + 1, total)
        return clean_text("\n\n".join(out))
    raise ValueError("Format non pris en charge (PNG, JPG, PDF...).")
