"""Detección explicable de fragmentos que podrían contener compromisos."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from src.ingest.pdf_loader import PaginaTexto


# Formas frecuentes del compromiso en planes de gobierno. Se mantiene público
# y pequeño para poder corregirlo con evidencia de falsos positivos/negativos.
_VERBOS_COMPROMISO = (
    "construiremos", "implementaremos", "ampliaremos", "fortaleceremos",
    "garantizaremos", "dotaremos", "crearemos", "rehabilitaremos",
    "mejoraremos", "incrementaremos", "reduciremos", "impulsaremos",
    "desarrollaremos", "ejecutaremos", "estableceremos", "promoveremos",
    "gestionaremos", "priorizaremos", "se construirá", "se implementará",
    # Los planes reales del CNE también formulan compromisos en infinitivo,
    # especialmente como objetivos numerados y listas de propuestas.
    "construir", "implementar", "ampliar", "fortalecer", "garantizar",
    "dotar", "crear", "rehabilitar", "mejorar", "incrementar", "reducir",
    "impulsar", "desarrollar", "ejecutar", "establecer", "promover",
    "gestionar", "priorizar", "consolidar", "reforzar", "fomentar",
    "asegurar", "proteger", "reactivar", "proponer", "continuar",
)
_PATRON_COMPROMISO = re.compile(r"\b(?:" + "|".join(re.escape(verbo) for verbo in _VERBOS_COMPROMISO) + r")\b", re.IGNORECASE)
_PATRON_EXCLUSION = re.compile(r"^(diagn[oó]stico|antecedentes|marco legal|contexto|justificaci[oó]n)\b", re.IGNORECASE)


@dataclass(frozen=True)
class FragmentoPromesa:
    texto: str
    pagina: int
    indice_en_pagina: int


def _unidades_de_texto(texto: str) -> list[str]:
    """Conserva párrafos; en PDFs sin saltos, usa oración como unidad mínima."""
    # pdfplumber conserva salto de línea por el ancho de página, pero no
    # siempre conserva párrafos. Las listas numeradas son las unidades más
    # fiables de compromiso en los planes revisados del CNE.
    bloques = re.split(r"\n\s*(?=(?:[-•]\s*\d|\d+(?:\.\d+)*[.)]\s+))", texto)
    parrafos = [re.sub(r"\s+", " ", parte).strip() for parte in bloques if parte.strip()]
    unidades: list[str] = []
    for parrafo in parrafos:
        if len(parrafo) > 1100:
            unidades.extend(parte.strip() for parte in re.split(r"(?<=[.;!?])\s+", parrafo) if parte.strip())
        else:
            unidades.append(parrafo)
    return unidades


def segmentar_documento(paginas: Iterable[PaginaTexto]) -> list[FragmentoPromesa]:
    fragmentos: list[FragmentoPromesa] = []
    vistos: set[tuple[int, str]] = set()
    en_diagnostico = False
    for pagina in paginas:
        # Los diagnósticos de planes reales suelen atravesar varias páginas;
        # un verbo en esa sección describe hechos pasados, no un compromiso.
        texto_pagina = pagina.texto.casefold()
        if "diagnóstico" in texto_pagina or "diagnostico" in texto_pagina:
            en_diagnostico = True
        if re.search(r"\b(?:objetivos?|propuestas?)\b", texto_pagina):
            en_diagnostico = False
        if en_diagnostico:
            continue
        for indice, texto in enumerate(_unidades_de_texto(pagina.texto), start=1):
            clave = (pagina.numero, texto.casefold())
            if clave in vistos or _PATRON_EXCLUSION.match(texto) or not _PATRON_COMPROMISO.search(texto):
                continue
            vistos.add(clave)
            fragmentos.append(FragmentoPromesa(texto=texto, pagina=pagina.numero, indice_en_pagina=indice))
    return fragmentos
