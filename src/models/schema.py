"""Modelos ligeros y serializables para evidencia electoral.

No imponen inferencias: los valores ausentes se conservan como ``None`` o
``no_especificado`` para que la interfaz pueda declararlos explícitamente.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from config import NIVEL_NO_DISPONIBLE


@dataclass
class Candidato:
    id: str
    nombre: str
    plan_gobierno_url: str
    proceso_electoral_id: str | None = None
    dignidad: str | None = None
    organizacion_politica: str | None = None


@dataclass
class FuenteHistorica:
    nombre_fuente: str
    url_o_id: str
    fecha_consulta: date
    fragmento_original: str
    anio: int | None = None
    valor: float | int | None = None
    unidad: str | None = None


@dataclass
class Calculo:
    nombre: str
    resultado: float
    formula: str
    descripcion: str = ""


@dataclass
class Promesa:
    id: str
    candidato: str
    categoria: str
    accion: str
    objeto: str
    texto_original: str
    fuente_documento: str
    pagina_o_seccion: str
    cantidad: float | int | None = None
    unidad: str | None = None
    presupuesto: float | int | str | None = None
    plazo: str | None = None
    indicador: str | None = None
    contexto_historico: list[FuenteHistorica] = field(default_factory=list)
    calculos: list[Calculo] = field(default_factory=list)
    nivel_comparacion: str = NIVEL_NO_DISPONIBLE
    metadata_ia: dict[str, Any] = field(default_factory=dict)
