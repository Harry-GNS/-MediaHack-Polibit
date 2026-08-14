"""Estructuración con IA con un contrato de no inferencia y trazabilidad."""
from __future__ import annotations

import json
import re
from typing import Any, Iterable

from config import NO_ESPECIFICADO, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from src.extraction.segmenter import FragmentoPromesa
from src.models.schema import Promesa


class ConfiguracionIAError(RuntimeError):
    pass


_CAMPOS = ("categoria", "accion", "objeto", "cantidad", "unidad", "presupuesto", "plazo", "indicador")


def _prompt(fragmento: FragmentoPromesa) -> str:
    return f"""Extrae UNA propuesta electoral del texto entre etiquetas y responde sólo JSON.
Reglas no negociables:
- Copia exclusivamente datos explícitos. No calcules, no completes ni evalúes.
- Para texto ausente usa exactamente \"{NO_ESPECIFICADO}\".
- cantidad y presupuesto deben ser número sólo si el texto muestra un número inequívoco.
- categoria puede ser \"{NO_ESPECIFICADO}\" si no se expresa.
- No escribas conclusiones políticas ni adjetivos de viabilidad o veracidad.
JSON esperado: {{"categoria": str, "accion": str, "objeto": str, "cantidad": number|string,
"unidad": str, "presupuesto": number|string, "plazo": str, "indicador": str}}
<texto pagina=\"{fragmento.pagina}\">{fragmento.texto}</texto>"""


def _contenido_respuesta(respuesta: Any) -> str:
    # Respuesta OpenAI-compatible de OpenRouter.
    elecciones = getattr(respuesta, "choices", None)
    if elecciones:
        return elecciones[0].message.content or ""
    # Compatible con los dobles de prueba y facilita diagnosticar respuestas
    # de proveedores que mantengan una forma distinta.
    contenido = getattr(respuesta, "content", respuesta)
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        return "".join(getattr(bloque, "text", "") for bloque in contenido)
    return str(contenido)


def _json_de_respuesta(texto: str) -> dict[str, Any]:
    coincidencia = re.search(r"\{.*\}", texto, re.DOTALL)
    if not coincidencia:
        raise ValueError("La IA no devolvió un objeto JSON")
    datos = json.loads(coincidencia.group(0))
    if not isinstance(datos, dict):
        raise ValueError("La IA no devolvió un objeto JSON")
    return {campo: datos.get(campo, NO_ESPECIFICADO) for campo in _CAMPOS}


def _cliente_por_defecto() -> Any:
    if not OPENROUTER_API_KEY:
        raise ConfiguracionIAError("Falta OPENROUTER_API_KEY; no se usará una IA simulada para datos reales.")
    if not OPENROUTER_MODEL:
        raise ConfiguracionIAError("Falta OPENROUTER_MODEL; selecciónalo explícitamente para evitar costos o modelos inesperados.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConfiguracionIAError("No está instalado el paquete openai.") from exc
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def estructurar_documento(
    fragmentos: Iterable[FragmentoPromesa], candidato_id: str, fuente_documento: str, cliente: Any | None = None
) -> list[Promesa]:
    cliente = cliente or _cliente_por_defecto()
    promesas: list[Promesa] = []
    for indice, fragmento in enumerate(fragmentos, start=1):
        respuesta = cliente.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": _prompt(fragmento)}],
        )
        datos = _json_de_respuesta(_contenido_respuesta(respuesta))
        promesas.append(
            Promesa(
                id=f"{candidato_id}-p{fragmento.pagina}-{indice}",
                candidato=candidato_id,
                categoria=str(datos["categoria"]),
                accion=str(datos["accion"]),
                objeto=str(datos["objeto"]),
                cantidad=datos["cantidad"] if isinstance(datos["cantidad"], (int, float)) else None,
                unidad=None if datos["unidad"] == NO_ESPECIFICADO else str(datos["unidad"]),
                presupuesto=datos["presupuesto"],
                plazo=None if datos["plazo"] == NO_ESPECIFICADO else str(datos["plazo"]),
                indicador=None if datos["indicador"] == NO_ESPECIFICADO else str(datos["indicador"]),
                texto_original=fragmento.texto,
                fuente_documento=fuente_documento,
                pagina_o_seccion=str(fragmento.pagina),
                metadata_ia={"proveedor": "openrouter", "modelo": OPENROUTER_MODEL, "fragmento_indice": fragmento.indice_en_pagina},
            )
        )
    return promesas
