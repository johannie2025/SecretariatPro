"""Facturation pour tiers : Facture / Proforma / Devis, calculs et PDF."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .numwords import amount_in_words
from .paths import client_dir, safe_name

DOC_TYPES = {"Facture": "FAC", "Proforma": "PRO", "Devis": "DEV"}
ACCENT = colors.HexColor("#1F5FBF")
LABELS = {
    "fr": {"types": {"Facture": "Facture", "Proforma": "Proforma", "Devis": "Devis"}, "no": "N°", "date": "Date :",
           "to": "Destinataire", "cols": ("Désignation", "Qté", "Prix unitaire", "Montant"), "sub": "Sous-total",
           "disc": "Remise", "tax": "Taxe / TVA", "total": "TOTAL TTC", "notes": "Notes / Conditions",
           "footer": "Document généré avec SecretariatPro — W Design",
           "lead": {"Facture": "Arrêtée la présente facture", "Proforma": "Arrêtée la présente proforma",
                    "Devis": "Arrêté le présent devis"}, "sum": "à la somme de :"},
    "es": {"types": {"Facture": "Factura", "Proforma": "Factura proforma", "Devis": "Presupuesto"}, "no": "N.º", "date": "Fecha:",
           "to": "Cliente", "cols": ("Descripción", "Cant.", "Precio unitario", "Importe"), "sub": "Subtotal",
           "disc": "Descuento", "tax": "Impuesto / IVA", "total": "TOTAL", "notes": "Notas / Condiciones",
           "footer": "Documento generado con SecretariatPro — W Design",
           "lead": {"Facture": "Se cierra la presente factura", "Proforma": "Se cierra la presente proforma",
                    "Devis": "Se cierra el presente presupuesto"}, "sum": "en la cantidad de:"},
    "en": {"types": {"Facture": "Invoice", "Proforma": "Proforma invoice", "Devis": "Quotation"}, "no": "No.", "date": "Date:",
           "to": "Bill to", "cols": ("Description", "Qty", "Unit price", "Amount"), "sub": "Subtotal",
           "disc": "Discount", "tax": "Tax / VAT", "total": "TOTAL", "notes": "Notes / Terms",
           "footer": "Document generated with SecretariatPro — W Design",
           "lead": {"Facture": "This invoice is closed", "Proforma": "This proforma invoice is closed",
                    "Devis": "This quotation is closed"}, "sum": "at the sum of:"},
}
_SEP = {"fr": (" ", ","), "es": (".", ","), "en": (",", ".")}


def D(value) -> Decimal:
    try:
        return Decimal(str(value).replace(" ", "").replace("\u202f", "").replace(",", ".") or "0")
    except InvalidOperation:
        raise ValueError(f"Nombre invalide : {value!r}")


def compute_totals(items, discount_pct=0, tax_pct=0):
    subtotal = sum((D(i["qty"]) * D(i["price"]) for i in items), Decimal("0"))
    discount = subtotal * D(discount_pct) / 100
    net = subtotal - discount
    tax = net * D(tax_pct) / 100
    return {"subtotal": subtotal, "discount": discount, "net": net, "tax": tax, "total": net + tax}


def money(value, currency="FCFA", lang="fr") -> str:
    th, dec = _SEP.get(lang, _SEP["fr"])
    v = Decimal(value)
    if currency in ("FCFA", "XAF", "XOF"):
        return f"{int(v.quantize(Decimal('1'), ROUND_HALF_UP)):,}".replace(",", th) + f" {currency}"
    raw = f"{v.quantize(Decimal('0.01'), ROUND_HALF_UP):,.2f}"
    return raw.replace(",", "\x00").replace(".", dec).replace("\x00", th) + f" {currency}"


def _logo_flowable(path, max_w=45 * mm, max_h=22 * mm):
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as im:
            w, h = im.size
        r = min(max_w / w, max_h / h)
        return Image(path, width=w * r, height=h * r, hAlign="LEFT")
    except Exception:
        return ""


def build_pdf(out_path, client, doc_type, number, issue_date, final_client, items,
              discount_pct, tax_pct, notes="", lang="fr"):
    L = LABELS.get(lang, LABELS["fr"])
    cur = client.get("currency", "FCFA")
    fm = lambda v: money(v, cur, lang)
    t = compute_totals(items, discount_pct, tax_pct)
    ss = getSampleStyleSheet()
    n = ParagraphStyle("n", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=13)
    b = ParagraphStyle("b", parent=n, fontName="Helvetica-Bold")
    title = ParagraphStyle("t", parent=n, fontName="Helvetica-Bold", fontSize=22, leading=28, textColor=ACCENT, alignment=2)
    small = ParagraphStyle("s", parent=n, fontSize=8, textColor=colors.grey, alignment=1)
    esc = lambda s: (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

    story = []
    company = [Paragraph(f"<b>{esc(client['name'])}</b>", ParagraphStyle("c", parent=n, fontSize=13))]
    for line in (client.get("address"), client.get("phone"), client.get("email")):
        if line:
            company.append(Paragraph(esc(line), n))
    ids = " — ".join(x for x in (f"NIF : {client['nif']}" if client.get("nif") else "",
                                  f"RCCM : {client['rccm']}" if client.get("rccm") else "") if x)
    if ids:
        company.append(Paragraph(esc(ids), n))
    logo = _logo_flowable(client["logo_path"]) if client.get("logo_path") and Path(client["logo_path"]).is_file() else ""
    left = [logo] + company if logo else company
    head = Table([[left, [Paragraph(L["types"].get(doc_type, doc_type).upper(), title),
                          Paragraph(f"{L['no']} <b>{esc(number)}</b><br/>{L['date']} {esc(issue_date)}",
                                    ParagraphStyle("r", parent=n, alignment=2))]]],
                 colWidths=[100 * mm, 80 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [head, Spacer(1, 8 * mm)]

    fc = [Paragraph(f"<b>{L['to']}</b>", n), Paragraph(esc(final_client.get("name")), b)]
    for k in ("address", "phone"):
        if final_client.get(k):
            fc.append(Paragraph(esc(final_client[k]), n))
    box = Table([[fc]], colWidths=[85 * mm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.lightgrey),
                             ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F7FB")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    box.hAlign = "LEFT"
    story += [box, Spacer(1, 8 * mm)]

    rows = [list(L["cols"])]
    for it in items:
        q, p = D(it["qty"]), D(it["price"])
        rows.append([Paragraph(esc(it["desc"]), n), f"{q.normalize():f}".replace(".", _SEP[lang][1] if lang in _SEP else ","), fm(p), fm(q * p)])
    tbl = Table(rows, colWidths=[85 * mm, 18 * mm, 38 * mm, 39 * mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FB")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [tbl, Spacer(1, 4 * mm)]

    tot = [[L["sub"], fm(t["subtotal"])]]
    if D(discount_pct) > 0:
        tot.append([f"{L['disc']} ({D(discount_pct).normalize():f} %)", "- " + fm(t["discount"])])
    if D(tax_pct) > 0:
        tot.append([f"{L['tax']} ({D(tax_pct).normalize():f} %)", fm(t["tax"])])
    tot.append([L["total"], fm(t["total"])])
    tt = Table(tot, colWidths=[45 * mm, 45 * mm], hAlign="RIGHT")
    tt.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                            ("BACKGROUND", (0, -1), (-1, -1), ACCENT), ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [tt]
    lead = L["lead"].get(doc_type, L["lead"]["Facture"])
    story += [Spacer(1, 5 * mm), Paragraph(f"{lead} {L['sum']} <b>{esc(amount_in_words(t['total'], cur, lang))}</b>.", n)]
    if notes.strip():
        story += [Spacer(1, 8 * mm), Paragraph(f"<b>{L['notes']}</b>", n), Paragraph(esc(notes), n)]
    story += [Spacer(1, 14 * mm), Paragraph(L["footer"], small)]

    SimpleDocTemplate(str(out_path), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=15 * mm, bottomMargin=15 * mm, title=f"{doc_type} {number}",
                      author=client["name"]).build(story)
    return t


def create_document(db, client_id, doc_type, final_client, items, discount_pct=0, tax_pct=0, notes="", lang="fr"):
    """Valide, génère le PDF, l'archive dans le dossier du client et l'enregistre."""
    if doc_type not in DOC_TYPES:
        raise ValueError("Type de document inconnu.")
    client = db.get_client(client_id)
    if not client:
        raise ValueError("Choisissez un entrepreneur.")
    if not final_client.get("name", "").strip():
        raise ValueError("Indiquez le nom du client final.")
    clean = [i for i in items if str(i.get("desc", "")).strip()]
    if not clean:
        raise ValueError("Ajoutez au moins une ligne.")
    for i in clean:
        if D(i["qty"]) <= 0 or D(i["price"]) < 0:
            raise ValueError("Quantités et prix doivent être positifs.")
    number = db.next_number(DOC_TYPES[doc_type])
    today = date.today()
    sub = "Factures_Emises" if doc_type == "Facture" else "Devis_Proforma"
    folder = client_dir(client["name"], sub)
    out = folder / f"{today.isoformat()}_{number}_{safe_name(final_client['name'])}.pdf"
    totals = build_pdf(out, client, doc_type, number, today.strftime("%d/%m/%Y"),
                       final_client, clean, discount_pct, tax_pct, notes, lang)
    db.add_document(client_id, doc_type, number, today.isoformat(), final_client["name"].strip(),
                    totals["total"], client.get("currency", "FCFA"), out)
    return out, number, totals
