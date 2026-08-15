"""
src/validation/validator.py
Motor de validación: compara los datos extraídos del texto
contra el contenido scrapeado de las fuentes usando OpenRouter.
"""
import json
import re
import unicodedata
from typing import Literal, Optional

import requests
from pydantic import BaseModel

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from src.validation.extractor import DatoEstadistico

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_CARACTERES_FUENTE = 8_000

_SYSTEM_PROMPT = (
    "Eres un asistente de verificación periodística. "
    "Tu rol es comparar la afirmación o texto del usuario contra el contenido de una fuente. "
    "NUNCA emitas juicios de valor ni digas si algo es verdadero o falso, limítate a indicar si la fuente lo menciona y en qué términos. "
    "Si la fuente habla del mismo evento y los datos generales coinciden, pon 'concordante'. Si contradicen directamente, pon 'discrepante'. "
    "Solo usa 'no_encontrado' si la fuente no menciona nada al respecto. "
    "CÁLCULO DEL PORCENTAJE (0-100): Sé EXTREMADAMENTE ESTRICTO. Un 100% significa que TODOS los datos duros (números, cifras, ubicaciones exactas) coinciden de manera idéntica. "
    "Si la noticia es la misma pero difieren en precisión (ejemplo: '100 km' vs '107 km', o 'más de 100' vs '100 exactos'), debes penalizar el porcentaje y asignarle entre 60% y 85% dependiendo de la magnitud de la diferencia. "
    "Responde exclusivamente con JSON válido."
)

_USER_PROMPT_TEMPLATE = """
Texto ingresado por el usuario a validar:
"{texto_original}"

Contenido de la fuente "{url}":
---
{contenido_fuente}
---

Analiza si la información del texto ingresado aparece o está respaldada por el contenido de la fuente.
Responde ÚNICAMENTE con este JSON (sin texto adicional, sin markdown):
{{
  "estado": "concordante" | "discrepante" | "no_encontrado",
  "porcentaje": <número entero entre 0 y 100 indicando similitud o respaldo semántico>,
  "diferencias": "<explicación detallada de en qué números, cifras o precisión difieren. O null si es 100% exacto>",
  "valor_en_fuente": "<fragmento o dato de la fuente que se relaciona, o null si no se encuentra>",
  "explicacion": "<una oración neutral describiendo lo encontrado, sin veredictos>"
}}
""".strip()


class ResultadoValidacion(BaseModel):
    dato: DatoEstadistico
    estado: Literal["concordante", "discrepante", "no_encontrado"]
    porcentaje: int
    diferencias: Optional[str] = None
    fuente_url: Optional[str] = None
    valor_en_fuente: Optional[str] = None
    alerta: str


_PALABRAS_COMUNES = {
    "a", "al", "ante", "con", "de", "del", "el", "en", "es", "la", "las",
    "lo", "los", "más", "para", "por", "que", "se", "su", "un", "una", "y",
}


def _terminos(texto: str) -> set[str]:
    """Normaliza términos relevantes para un respaldo local transparente."""
    texto_normalizado = unicodedata.normalize("NFD", texto.lower())
    texto_normalizado = "".join(
        caracter for caracter in texto_normalizado if unicodedata.category(caracter) != "Mn"
    )
    return {
        termino
        for termino in re.findall(r"[a-z0-9]+", texto_normalizado)
        if len(termino) > 2 and termino not in _PALABRAS_COMUNES
    }


def _respaldo_local(dato: DatoEstadistico, fuente: dict, motivo: str) -> ResultadoValidacion:
    """Devuelve la cita más relacionada si la IA no está disponible.

    No infiere contradicciones: sólo marca concordancia cuando la mayoría de
    términos significativos de la afirmación aparece en un fragmento textual.
    """
    from app import texto_completo

    consulta = _terminos(dato.texto_original)
    fragmentos = [
        str(fuente.get("titulo") or ""),
        *[str(encabezado.get("texto") or "") for encabezado in fuente.get("encabezados", [])],
        *[str(parrafo) for parrafo in fuente.get("parrafos", [])],
    ]
    mejor_fragmento = ""
    mejor_puntaje = 0.0
    for fragmento in fragmentos:
        if not fragmento:
            continue
        terminos_fragmento = _terminos(fragmento)
        puntaje = len(consulta & terminos_fragmento) / len(consulta) if consulta else 0.0
        if puntaje > mejor_puntaje:
            mejor_fragmento, mejor_puntaje = fragmento, puntaje

    porcentaje = round(mejor_puntaje * 100)
    concordante = mejor_puntaje >= 0.70
    estado: Literal["concordante", "discrepante", "no_encontrado"] = (
        "concordante" if concordante else "no_encontrado"
    )
    if concordante:
        alerta = (
            "Respaldo local activado (IA no disponible: "
            f"{motivo}); coincidencia textual encontrada en la fuente."
        )
    else:
        alerta = (
            "Respaldo local activado (IA no disponible: "
            f"{motivo}); no se halló una coincidencia textual suficiente en la fuente."
        )
    return ResultadoValidacion(
        dato=dato,
        estado=estado,
        porcentaje=porcentaje if concordante else 0,
        diferencias=None,
        fuente_url=fuente.get("url"),
        valor_en_fuente=mejor_fragmento[:600] if mejor_puntaje else None,
        alerta=alerta,
    )


def _llamar_openrouter(prompt_usuario: str) -> dict:
    """Llama a OpenRouter y retorna el JSON parseado de la respuesta."""
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("OPENROUTER_API_KEY no está configurada en las variables de entorno.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://evidencia-electoral.ec",
        "X-Title": "Evidencia Electoral",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario},
        ],
        "temperature": 0.0,
        # El router gratuito prioriza modelos que admiten salida estructurada;
        # exigir JSON evita respuestas de texto libre que no puede consumir la UI.
        "response_format": {"type": "json_object"},
        # gpt-oss puede usar parte de la salida para razonamiento antes de
        # generar el JSON; este margen evita respuestas truncadas.
        "max_tokens": 500,
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"].get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("El modelo no alcanzó a generar una respuesta JSON utilizable.")
    content = content.strip()

    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        content = match.group(0)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error parseando JSON de OpenRouter: {content}")
        raise e


def validar_texto(texto: str, fuentes_scrapeadas: list[dict]) -> list[ResultadoValidacion]:
    """
    Valida el texto completo contra cada una de las fuentes y retorna un resultado por fuente.
    """
    from src.validation.extractor import DatoEstadistico

    dato = DatoEstadistico(
        texto_original=texto,
        valor=0.0,
        unidad="",
        contexto="Validación de texto completo"
    )

    resultados_por_fuente = []

    # Evita gastar una llamada de IA si no hay una afirmación que contrastar.
    # Esto también da una respuesta clara en vez de un falso error de proveedor.
    if len(texto.strip()) < 8:
        return [
            ResultadoValidacion(
                dato=dato,
                estado="no_encontrado",
                porcentaje=0,
                diferencias=None,
                fuente_url=fuente.get("url"),
                valor_en_fuente=None,
                alerta="Escribe una afirmación o dato concreto para contrastarlo con la fuente.",
            )
            for fuente in fuentes_scrapeadas
        ]

    for fuente in fuentes_scrapeadas:
        if fuente.get("error"):
            # Generamos un resultado de fallo para esta fuente
            resultados_por_fuente.append(
                ResultadoValidacion(
                    dato=dato,
                    estado="no_encontrado",
                    porcentaje=0,
                    diferencias=None,
                    fuente_url=fuente.get("url"),
                    valor_en_fuente=None,
                    alerta=f"Error al extraer la fuente: {fuente['error']}"
                )
            )
            continue

        # Construir texto de la fuente
        from app import texto_completo
        # Un extracto acotado reduce latencia y uso de contexto en modelos
        # gratuitos, sin enviar navegación, menús ni el documento completo.
        contenido = texto_completo(fuente)[:MAX_CARACTERES_FUENTE]

        prompt = _USER_PROMPT_TEMPLATE.format(
            texto_original=dato.texto_original,
            url=fuente["url"],
            contenido_fuente=contenido,
        )

        try:
            respuesta = _llamar_openrouter(prompt)
            estado = respuesta.get("estado", "no_encontrado")
            porcentaje = respuesta.get("porcentaje", 0)
            diferencias = respuesta.get("diferencias")
            valor_fuente = respuesta.get("valor_en_fuente")
            explicacion = respuesta.get("explicacion", "Sin información adicional.")

            # Validación de porcentaje
            if not isinstance(porcentaje, int):
                try:
                    porcentaje = int(porcentaje)
                except ValueError:
                    porcentaje = 0

            resultados_por_fuente.append(
                ResultadoValidacion(
                    dato=dato,
                    estado=estado,
                    porcentaje=porcentaje,
                    diferencias=diferencias,
                    fuente_url=fuente["url"],
                    valor_en_fuente=valor_fuente,
                    alerta=explicacion,
                )
            )
        except requests.HTTPError as e:
            codigo = e.response.status_code if e.response is not None else "desconocido"
            resultados_por_fuente.append(_respaldo_local(dato, fuente, f"HTTP {codigo}"))
        except (requests.RequestException, json.JSONDecodeError, KeyError, ValueError, EnvironmentError) as e:
            resultados_por_fuente.append(_respaldo_local(dato, fuente, str(e)))

    return resultados_por_fuente

