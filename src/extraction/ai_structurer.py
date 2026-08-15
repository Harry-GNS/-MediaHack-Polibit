"""Estructuración con IA con un contrato de no inferencia y trazabilidad."""
from __future__ import annotations

import json
import re
from typing import Any, Iterable

from config import (
    NO_ESPECIFICADO,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_BATCH_SIZE,
    OPENROUTER_MAX_OUTPUT_TOKENS,
    OPENROUTER_MODEL,
    OPENROUTER_TIMEOUT_SECONDS,
)
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


def _prompt_lote(fragmentos: list[FragmentoPromesa]) -> str:
    if len(fragmentos) == 1:
        return _prompt(fragmentos[0])
    textos = "\n".join(
        f'<texto indice="{indice}" pagina="{fragmento.pagina}">{fragmento.texto}</texto>'
        for indice, fragmento in enumerate(fragmentos)
    )
    return f"""Extrae exactamente UNA propuesta electoral por cada texto y responde sólo un arreglo JSON.
Reglas no negociables:
- Devuelve {len(fragmentos)} objetos, en el mismo orden de los textos.
- Copia exclusivamente datos explícitos. No calcules, no completes ni evalúes.
- Para texto ausente usa exactamente \"{NO_ESPECIFICADO}\".
- cantidad y presupuesto deben ser número sólo si el texto muestra un número inequívoco.
- categoria puede ser \"{NO_ESPECIFICADO}\" si no se expresa.
- No escribas conclusiones políticas ni adjetivos de viabilidad o veracidad.
Cada objeto debe tener: categoria, accion, objeto, cantidad, unidad, presupuesto, plazo, indicador.
{textos}"""


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


def _json_lote_de_respuesta(texto: str, cantidad: int) -> list[dict[str, Any]]:
    if cantidad == 1:
        return [_json_de_respuesta(texto)]
    coincidencia = re.search(r"\[.*\]", texto, re.DOTALL)
    if not coincidencia:
        raise ValueError("La IA no devolvió un arreglo JSON para el lote")
    datos = json.loads(coincidencia.group(0))
    if not isinstance(datos, list) or len(datos) != cantidad or not all(isinstance(item, dict) for item in datos):
        raise ValueError(f"La IA devolvió un lote inválido: se esperaban {cantidad} propuestas")
    return [{campo: item.get(campo, NO_ESPECIFICADO) for campo in _CAMPOS} for item in datos]


def _cliente_por_defecto() -> Any:
    if not OPENROUTER_API_KEY:
        raise ConfiguracionIAError("Falta OPENROUTER_API_KEY; no se usará una IA simulada para datos reales.")
    if not OPENROUTER_MODEL:
        raise ConfiguracionIAError("Falta OPENROUTER_MODEL; selecciónalo explícitamente para evitar costos o modelos inesperados.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConfiguracionIAError("No está instalado el paquete openai.") from exc
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
        timeout=OPENROUTER_TIMEOUT_SECONDS,
        # Un error se muestra de inmediato; reintentos silenciosos harían que
        # la consola vuelva a parecer bloqueada durante varios minutos.
        max_retries=0,
    )


def _estructurar_lote(cliente: Any, lote: list[FragmentoPromesa]) -> list[dict[str, Any]]:
    """Solicita un lote y degrada a sublotes si el proveedor lo trunca."""
    respuesta = cliente.chat.completions.create(
        model=OPENROUTER_MODEL,
        # Nunca se reserva más del límite local. Si la salida se trunca, este
        # mismo método reduce el lote en vez de pedir un crédito mayor.
        max_tokens=min(OPENROUTER_MAX_OUTPUT_TOKENS, max(400, 100 * len(lote))),
        temperature=0,
        messages=[{"role": "user", "content": _prompt_lote(lote)}],
    )
    try:
        return _json_lote_de_respuesta(_contenido_respuesta(respuesta), len(lote))
    except ValueError:
        if len(lote) == 1:
            raise
        mitad = len(lote) // 2
        print(f"[4/6] Respuesta incompleta; reintentando en sublotes de {mitad} y {len(lote) - mitad}…", flush=True)
        return _estructurar_lote(cliente, lote[:mitad]) + _estructurar_lote(cliente, lote[mitad:])


def estructurar_documento(
    fragmentos: Iterable[FragmentoPromesa],
    candidato_id: str,
    fuente_documento: str,
    cliente: Any | None = None,
    max_fragmentos: int | None = None,
) -> list[Promesa]:
    cliente = cliente or _cliente_por_defecto()
    lista_fragmentos = list(fragmentos)
    total_fragmentos = len(lista_fragmentos)
    if max_fragmentos is not None:
        if max_fragmentos < 1:
            raise ValueError("max_fragmentos debe ser mayor que cero")
        if len(lista_fragmentos) > max_fragmentos:
            lista_fragmentos = _muestra_distribuida(lista_fragmentos, max_fragmentos)
            print(
                f"[4/6] Modo rápido: se procesarán {len(lista_fragmentos)} de "
                f"{total_fragmentos} fragmentos, distribuidos por página.",
                flush=True,
            )
    tamanio_lote = max(1, OPENROUTER_BATCH_SIZE)
    promesas: list[Promesa] = []
    total_lotes = (len(lista_fragmentos) + tamanio_lote - 1) // tamanio_lote
    for numero_lote, inicio in enumerate(range(0, len(lista_fragmentos), tamanio_lote), start=1):
        lote = lista_fragmentos[inicio : inicio + tamanio_lote]
        print(f"[4/6] Estructurando lote {numero_lote}/{total_lotes} ({len(lote)} fragmentos)…", flush=True)
        datos_lote = _estructurar_lote(cliente, lote)
        for fragmento, datos in zip(lote, datos_lote, strict=True):
            indice = len(promesas) + 1
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
                    metadata_ia={
                        "proveedor": "openrouter",
                        "modelo": OPENROUTER_MODEL,
                        "fragmento_indice": fragmento.indice_en_pagina,
                        "lote": numero_lote,
                    },
                )
            )
    return promesas


def _muestra_distribuida(fragmentos: list[FragmentoPromesa], limite: int) -> list[FragmentoPromesa]:
    """Muestra el documento completo sin sesgarse hacia sus primeras páginas."""
    if len(fragmentos) <= limite:
        return fragmentos
    posiciones = [round(indice * (len(fragmentos) - 1) / (limite - 1)) for indice in range(limite)] if limite > 1 else [0]
    return [fragmentos[posicion] for posicion in posiciones]


def estructurar_documento_local(
    fragmentos: Iterable[FragmentoPromesa], candidato_id: str, fuente_documento: str, max_fragmentos: int | None = None
) -> list[Promesa]:
    """Convierte fragmentos trazables a evidencia sin llamar a un proveedor IA."""
    lista_fragmentos = list(fragmentos)
    if max_fragmentos is not None and len(lista_fragmentos) > max_fragmentos:
        lista_fragmentos = _muestra_distribuida(lista_fragmentos, max_fragmentos)
    promesas: list[Promesa] = []
    for indice, fragmento in enumerate(lista_fragmentos, start=1):
        accion = re.search(
            r"\b(construir(?:emos)?|implementar(?:emos)?|mejorar(?:emos)?|ampliar(?:emos)?|fortalecer(?:emos)?|"
            r"crear(?:emos)?|promover(?:emos)?|garantizar(?:emos)?|reducir(?:emos)?|desarrollar(?:emos)?)\b",
            fragmento.texto,
            re.IGNORECASE,
        )
        promesas.append(
            Promesa(
                id=f"{candidato_id}-p{fragmento.pagina}-{indice}",
                candidato=candidato_id,
                categoria=NO_ESPECIFICADO,
                accion=accion.group(1).capitalize() if accion else "Propuesta",
                objeto=fragmento.texto[:180].strip(),
                cantidad=None,
                unidad=None,
                presupuesto=NO_ESPECIFICADO,
                plazo=None,
                indicador=None,
                texto_original=fragmento.texto,
                fuente_documento=fuente_documento,
                pagina_o_seccion=str(fragmento.pagina),
                metadata_ia={"modo": "local_sin_ia", "fragmento_indice": fragmento.indice_en_pagina},
            )
        )
    return promesas
