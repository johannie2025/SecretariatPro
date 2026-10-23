"""Import paresseux de PyMuPDF : une bibliothèque manquante ne bloque plus l'ouverture de l'application."""


class _LazyFitz:
    _mod = None

    def __getattr__(self, name):
        if _LazyFitz._mod is None:
            try:
                import pymupdf as mod
            except ImportError:      # anciennes versions
                import fitz as mod
            _LazyFitz._mod = mod
        return getattr(_LazyFitz._mod, name)


fitz = _LazyFitz()
