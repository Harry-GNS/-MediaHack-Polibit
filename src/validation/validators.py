"""Validaciones que separan ausencia de datos de errores de trazabilidad."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from config import NIVELES_COMPARACION, NO_ESPECIFICADO
from src.models.schema import Promesa


@dataclass
class ResultadoValidacion:
    valida: bool
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


_PATRONES_JUICIO = re.compile(
    r"\b(inviable|viable|fals[oa]|miente|mentira|engaños[oa]|bueno|malo)\b",
    re.IGNORECASE,
)


def contiene_lenguaje_de_juicio(texto: str) -> bool:
    """Detecta términos prohibidos para alertas, no para el texto fuente."""
    return bool(_PATRONES_JUICIO.search(texto or ""))


def _no_especificado(valor: object) -> bool:
    return valor is None or valor == "" or valor == NO_ESPECIFICADO


def validar_promesa(promesa: Promesa) -> ResultadoValidacion:
    errores: list[str] = []
    advertencias: list[str] = []
    for campo in ("id", "candidato", "accion", "objeto", "texto_original", "fuente_documento", "pagina_o_seccion"):
        if not getattr(promesa, campo, None):
            errores.append(f"{campo} es obligatorio para mantener trazabilidad")
    if promesa.nivel_comparacion not in NIVELES_COMPARACION:
        errores.append("nivel_comparacion no es válido")
    for campo, etiqueta in (("presupuesto", "Presupuesto"), ("plazo", "Plazo"), ("indicador", "Indicador")):
        if _no_especificado(getattr(promesa, campo, None)):
            advertencias.append(f"{etiqueta} no especificado en el plan.")
    return ResultadoValidacion(valida=not errores, errores=errores, advertencias=advertencias)
