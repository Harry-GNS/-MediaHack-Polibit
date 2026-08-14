"""Extracción de texto conservando la página como parte de la evidencia."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pdfplumber


class PDFSinTextoError(ValueError):
    """El PDF no contiene texto aprovechable por el MVP."""


@dataclass(frozen=True)
class PaginaTexto:
    numero: int
    texto: str


def extraer_texto_por_pagina(ruta_pdf: str | Path) -> list[PaginaTexto]:
    ruta = Path(ruta_pdf)
    if ruta.suffix.lower() != ".pdf" or not ruta.is_file():
        raise FileNotFoundError(f"No existe un PDF válido: {ruta}")
    paginas: list[PaginaTexto] = []
    with pdfplumber.open(ruta) as pdf:
        for numero, pagina in enumerate(pdf.pages, start=1):
            texto = (pagina.extract_text() or "").strip()
            paginas.append(PaginaTexto(numero=numero, texto=texto))
    if not any(pagina.texto for pagina in paginas):
        raise PDFSinTextoError("El PDF parece escaneado o no contiene texto. El MVP no aplica OCR automáticamente.")
    return paginas
