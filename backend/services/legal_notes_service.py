from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path


REFERENCE_PDF_PATH = Path("pdf/CONTRATO ARRAS PENITENCIALES.docx (1).pdf")

FALLBACK_CLAUSES: dict[str, str] = {
    "clause_1": (
        "El precio de venta es de {{total_price_eur}} EUR. "
        "La parte compradora ({{buyers_names}}) entrega en este acto a la parte vendedora "
        "({{sellers_names}}) la cantidad de {{arras_amount_eur}} EUR en concepto de arras penitenciales, "
        "de conformidad con el artículo 621.8 del Libro VI del Código Civil de Cataluña."
    ),
    "clause_2": (
        "La cantidad restante del precio, {{remaining_amount_eur}} EUR, se abonará en el otorgamiento "
        "de la escritura pública de compraventa antes del día {{deadline_date}}. "
        "Si la parte compradora incumple, perderá las arras; si incumple la parte vendedora, "
        "devolverá las arras duplicadas."
    ),
    "clause_3": (
        "La compraventa de la finca {{property_address}} se formalizará libre de cargas, gravámenes, "
        "ocupantes o arrendatarios, y al corriente de pago de impuestos y gastos comunitarios, "
        "salvo pacto expreso en contrario."
    ),
    "clause_4": (
        "Todos los gastos e impuestos derivados de la escritura pública de compraventa serán a cargo "
        "de la parte compradora, con excepción de la plusvalía municipal, que corresponderá a la parte vendedora, "
        "de conformidad con la normativa civil catalana aplicable."
    ),
    "clause_5": (
        "La parte compradora declara haber recibido con anterioridad a este acto la información y documentación "
        "legal exigible para la transmisión, incluyendo nota simple y ficha catastral, en los términos previstos "
        "por la normativa de vivienda aplicable a segundas y ulteriores transmisiones."
    ),
}

_CLAUSE_ORDINAL_TO_KEY = {
    "PRIMERA": "clause_1",
    "SEGUNDA": "clause_2",
    "TERCERA": "clause_3",
    "CUARTA": "clause_4",
    "QUINTA": "clause_5",
}

_CLAUSE_PATTERN = re.compile(
    r"\b(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA)\.\s*(.*?)(?=\b(?:PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA)\.|AS[IÍ]\s+LO\s+OTORGAN|$)",
    re.DOTALL | re.IGNORECASE,
)

_PLACEHOLDER_REQUIRED_BY_CLAUSE: dict[str, list[str]] = {
    "clause_1": ["{{buyers_names}}", "{{sellers_names}}", "{{total_price_eur}}", "{{arras_amount_eur}}"],
    "clause_2": ["{{remaining_amount_eur}}", "{{deadline_date}}"],
}


@lru_cache(maxsize=1)
def get_reference_clauses() -> dict[str, str]:
    text = _extract_reference_pdf_text(REFERENCE_PDF_PATH)
    extracted = _extract_clauses_from_text(text)
    if not extracted:
        return dict(FALLBACK_CLAUSES)

    tokenized = {key: _tokenize_clause_text(value) for key, value in extracted.items()}
    merged = dict(FALLBACK_CLAUSES)
    merged.update(tokenized)
    return {key: _ensure_required_placeholders(key, value) for key, value in merged.items()}


def _extract_reference_pdf_text(pdf_path: Path) -> str:
    if not pdf_path.exists():
        return ""
    try:
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except Exception:
        return ""


def _extract_clauses_from_text(text: str) -> dict[str, str]:
    if not text.strip():
        return {}
    normalized = _normalize_text(text)
    clauses: dict[str, str] = {}
    for ordinal, body in _CLAUSE_PATTERN.findall(normalized):
        key = _CLAUSE_ORDINAL_TO_KEY.get(ordinal.upper())
        if not key:
            continue
        cleaned_body = _clean_clause_text(body)
        if cleaned_body:
            clauses[key] = cleaned_body
    return clauses


def _normalize_text(text: str) -> str:
    text = text.replace("\f", "\n")
    text = re.sub(r"\n+", "\n", text)
    return text


def _clean_clause_text(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\bMODELO\s+COMPRAVENTA\s+CON\s+ARRAS\s+PENITENCIALES\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bP[áa]g\.\s*\d+\s*de\s*\d+\s*C\.S\.V\.[^ ]*", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?<=\s)\d+\s+(?=MODELO)", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(\d)\s+EUROS\b", "EUROS", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^\-\s*", "", cleaned)
    return cleaned


def _tokenize_clause_text(text: str) -> str:
    tokenized = text
    replacements = [
        (r"(?i)(la\s+parte\s+compradora)\s*\([^)]*\)", r"\1 ({{buyers_names}})"),
        (r"(?i)(la\s+parte\s+vendedora)\s*\([^)]*\)", r"\1 ({{sellers_names}})"),
        (r"45\.500€", "{{total_price_eur}}"),
        (r"4\.550€", "{{arras_amount_eur}}"),
        (r"40\.950€", "{{remaining_amount_eur}}"),
        (r"\b\d{1,2}\s+de\s+[A-Za-záéíóúñ]+\s+de\s+\d{4}\b", "{{deadline_date}}"),
    ]
    for pattern, replacement in replacements:
        tokenized = re.sub(pattern, replacement, tokenized)
    return tokenized


def _ensure_required_placeholders(clause_id: str, text: str) -> str:
    required = _PLACEHOLDER_REQUIRED_BY_CLAUSE.get(clause_id, [])
    if required and any(token not in text for token in required):
        return FALLBACK_CLAUSES[clause_id]
    return text
