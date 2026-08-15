"""Extracción de texto conservando la página como parte de la evidencia."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import pdfplumber
from pypdf import PdfReader
from src.extraction.text_normalizer import estandarizar_texto


class PDFSinTextoError(ValueError):
    """El PDF no contiene texto aprovechable por el MVP."""


@dataclass(frozen=True)
class PaginaTexto:
    numero: int
    texto: str


def _fragmentacion_de_palabras(texto: str) -> float:
    """Mide letras o sílabas aisladas, un síntoma común de PDFs tabulares."""
    palabras = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", texto)
    if not palabras:
        return float("inf")
    return sum(len(palabra) <= 2 for palabra in palabras) / len(palabras)


def _texto_mas_legible(texto_pdfplumber: str, texto_pypdf: str) -> str:
    """Escoge la extracción con palabras menos fragmentadas.

    Algunos planes contienen tablas cuyos glifos PDFplumber ordena por posición,
    separando letras; pypdf suele conservar mejor el orden lógico en ese caso.
    """
    opciones = [texto for texto in (texto_pdfplumber.strip(), texto_pypdf.strip()) if texto]
    if not opciones:
        return ""
    return min(opciones, key=_fragmentacion_de_palabras)


def extraer_texto_por_pagina(ruta_pdf: str | Path) -> list[PaginaTexto]:
    ruta = Path(ruta_pdf)
    if ruta.suffix.lower() != ".pdf" or not ruta.is_file():
        raise FileNotFoundError(f"No existe un PDF válido: {ruta}")
    paginas: list[PaginaTexto] = []
    with pdfplumber.open(ruta) as pdf:
        lector = PdfReader(str(ruta))
        for numero, pagina in enumerate(pdf.pages, start=1):
            texto_pdfplumber = pagina.extract_text() or ""
            texto_pypdf = lector.pages[numero - 1].extract_text() or "" if numero <= len(lector.pages) else ""
            texto = estandarizar_texto(_texto_mas_legible(texto_pdfplumber, texto_pypdf))
            paginas.append(PaginaTexto(numero=numero, texto=texto))
    if not any(pagina.texto for pagina in paginas):
        raise PDFSinTextoError("El PDF parece escaneado o no contiene texto. El MVP no aplica OCR automáticamente.")
    return paginas
