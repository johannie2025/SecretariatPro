"""Outils PDF : éditeur (texte, images, masquage), fusion, découpe, rotation, sécurité..."""
import re
from pathlib import Path

from ._lazy import fitz

COLORS = {"Noir": (0, 0, 0), "Rouge": (0.85, 0.1, 0.1), "Bleu": (0.1, 0.3, 0.8), "Vert": (0.1, 0.55, 0.2)}


def _open(path, password=None):
    doc = fitz.open(str(path))
    if doc.needs_pass and not (password and doc.authenticate(password)):
        doc.close()
        raise ValueError("Ce PDF est protégé : mot de passe requis ou incorrect.")
    return doc


def parse_pages(spec: str, n: int):
    """« 1-3,5,8- » → indices 0-based dans l'ordre saisi."""
    out = []
    for part in re.split(r"[,;\s]+", spec.strip()):
        if not part:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)", part)
        if m:
            a, b = int(m.group(1) or 1), int(m.group(2) or n)
            rng = range(a, b + 1) if a <= b else range(a, b - 1, -1)
        elif part.isdigit():
            rng = [int(part)]
        else:
            raise ValueError(f"Pages invalides : « {part} ».")
        for p in rng:
            if not 1 <= p <= n:
                raise ValueError(f"La page {p} n'existe pas (le document en compte {n}).")
            out.append(p - 1)
    if not out:
        raise ValueError("Indiquez au moins une page (ex. 1-3,5).")
    return out


def _save(doc, out):
    doc.save(str(out), garbage=3, deflate=True)
    return Path(out)


# ------------------------------------------------------------ organisation
def merge(paths, out):
    res = fitz.open()
    for p in paths:
        with _open(p) as d:
            res.insert_pdf(d)
    try:
        return _save(res, out)
    finally:
        res.close()


def extract_pages(path, spec, out):
    with _open(path) as d:
        idx = parse_pages(spec, len(d))
        d.select(idx)
        return _save(d, out)


def delete_pages(path, spec, out):
    with _open(path) as d:
        gone = set(parse_pages(spec, len(d)))
        keep = [i for i in range(len(d)) if i not in gone]
        if not keep:
            raise ValueError("Vous ne pouvez pas supprimer toutes les pages.")
        d.select(keep)
        return _save(d, out)


def split_each(path, out_dir, stem):
    out_dir = Path(out_dir)
    files = []
    with _open(path) as d:
        for i in range(len(d)):
            part = fitz.open()
            part.insert_pdf(d, from_page=i, to_page=i)
            files.append(_save(part, out_dir / f"{stem}_page{i + 1:03d}.pdf"))
            part.close()
    return files


def rotate_pages(path, spec, angle, out):
    with _open(path) as d:
        for i in (parse_pages(spec, len(d)) if spec.strip() else range(len(d))):
            d[i].set_rotation((d[i].rotation + angle) % 360)
        return _save(d, out)


# --------------------------------------------------------------- sécurité
def protect(path, out, password):
    if len(password) < 4:
        raise ValueError("Mot de passe trop court (4 caractères minimum).")
    with _open(path) as d:
        d.save(str(out), encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password + "#own", garbage=3, deflate=True)
    return Path(out)


def unprotect(path, out, password):
    with _open(path, password) as d:
        d.save(str(out), encryption=fitz.PDF_ENCRYPT_NONE, garbage=3, deflate=True)
    return Path(out)


def watermark(path, out, text, size=64, opacity=0.18):
    if not text.strip():
        raise ValueError("Saisissez le texte du filigrane.")
    with _open(path) as d:
        for page in d:
            r = page.rect
            c = fitz.Point(r.width * 0.18, r.height * 0.62)
            page.insert_text(c, text, fontsize=size, fontname="helv", color=(0.5, 0.5, 0.5),
                             fill_opacity=opacity, morph=(c, fitz.Matrix(-40)), overlay=True)
        return _save(d, out)


def number_pages(path, out, fmt="Page {n} / {N}"):
    with _open(path) as d:
        total = len(d)
        for i, page in enumerate(d):
            txt = fmt.replace("{n}", str(i + 1)).replace("{N}", str(total))
            w = fitz.get_text_length(txt, fontname="helv", fontsize=9)
            page.insert_text((page.rect.width / 2 - w / 2, page.rect.height - 22), txt,
                             fontsize=9, fontname="helv", color=(0.3, 0.3, 0.3))
        return _save(d, out)


def compress(path, out):
    with _open(path) as d:
        try:
            d.rewrite_images(dpi_threshold=170, dpi_target=130, quality=70)
        except Exception:
            pass
        d.save(str(out), garbage=4, deflate=True, clean=True)
    before, after = Path(path).stat().st_size, Path(out).stat().st_size
    return Path(out), before, after


# -------------------------------------------------------------- conversions
def images_to_pdf(paths, out):
    from PIL import Image
    doc = fitz.open()
    for p in paths:
        with Image.open(p) as im:
            w, h = im.size
        landscape = w > h
        page = doc.new_page(width=842 if landscape else 595, height=595 if landscape else 842)
        page.insert_image(fitz.Rect(20, 20, page.rect.width - 20, page.rect.height - 20),
                          filename=str(p), keep_proportion=True)
    try:
        return _save(doc, out)
    finally:
        doc.close()


def pdf_to_images(path, out_dir, stem, dpi=150):
    files = []
    with _open(path) as d:
        for i, page in enumerate(d):
            f = Path(out_dir) / f"{stem}_page{i + 1:03d}.png"
            page.get_pixmap(dpi=dpi, alpha=False).save(str(f))
            files.append(f)
    return files


# ------------------------------------------------------------------ éditeur
class PdfEditor:
    """Édition en mémoire avec annulation ; rien n'est écrit tant qu'on n'enregistre pas."""

    def __init__(self, path, password=None):
        with _open(path, password) as d:
            self._data = d.tobytes()
        self.doc = fitz.open("pdf", self._data)
        self.undo_stack = []

    @property
    def n(self):
        return len(self.doc)

    def page_size(self, i):
        r = self.doc[i].rect
        return r.width, r.height

    def render(self, i, zoom):
        return self.doc[i].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes("png")

    def _snapshot(self):
        self.undo_stack.append(self.doc.tobytes())
        del self.undo_stack[:-15]

    def undo(self):
        if not self.undo_stack:
            return False
        self.doc.close()
        self.doc = fitz.open("pdf", self.undo_stack.pop())
        return True

    def _pt(self, i, x, y):
        return fitz.Point(x, y) * self.doc[i].derotation_matrix

    def _rect(self, i, r):
        rect = fitz.Rect(*r) * self.doc[i].derotation_matrix
        rect.normalize()
        return rect

    def add_text(self, i, x, y, text, size=12, color="Noir"):
        if not text.strip():
            raise ValueError("Saisissez le texte à ajouter.")
        self._snapshot()
        p = self._pt(i, x, y)
        for k, line in enumerate(text.split("\n")):
            self.doc[i].insert_text((p.x, p.y + k * size * 1.25), line, fontsize=size,
                                    fontname="helv", color=COLORS.get(color, (0, 0, 0)))

    def add_image(self, i, rect, image_path):
        self._snapshot()
        self.doc[i].insert_image(self._rect(i, rect), filename=str(image_path), keep_proportion=True)

    def redact(self, i, rect, fill=(0, 0, 0)):
        self._snapshot()
        page = self.doc[i]
        page.add_redact_annot(self._rect(i, rect), fill=fill)
        page.apply_redactions()

    def replace_text(self, i, rect, text, size=None, color="Noir"):
        """Efface la zone (blanc) puis écrit le nouveau texte à sa place."""
        r = self._rect(i, rect)
        self.redact(i, rect, fill=(1, 1, 1))
        size = size or max(7, min(30, r.height * 0.72))
        self.doc[i].insert_text((r.x0 + 1, r.y1 - r.height * 0.22), text, fontsize=size,
                                fontname="helv", color=COLORS.get(color, (0, 0, 0)))

    def highlight(self, i, rect):
        self._snapshot()
        page = self.doc[i]
        page.draw_rect(self._rect(i, rect), color=None, fill=(1, 0.93, 0.2), fill_opacity=0.4, overlay=True)

    def rotate(self, i, angle=90):
        self._snapshot()
        self.doc[i].set_rotation((self.doc[i].rotation + angle) % 360)

    def delete_page(self, i):
        if self.n <= 1:
            raise ValueError("Impossible de supprimer la dernière page.")
        self._snapshot()
        self.doc.delete_page(i)

    def save(self, out):
        self.doc.save(str(out), garbage=3, deflate=True)
        return Path(out)
