"""
src/validation/validator.py
Motor de validación: compara los datos extraídos del texto
contra el contenido scrapeado de las fuentes usando OpenRouter.
"""
import json
import os
from typing import Literal, Optional

import requests
from pydantic import BaseModel

from src.validation.extractor import DatoEstadistico

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

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
        "max_tokens": 300,
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    import re
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
        contenido = texto_completo(fuente)[:30000]

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
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            resultados_por_fuente.append(
                ResultadoValidacion(
                    dato=dato,
                    estado="no_encontrado",
                    porcentaje=0,
                    diferencias=None,
                    fuente_url=fuente["url"],
                    valor_en_fuente=None,
                    alerta=f"Error procesando la fuente con IA: {str(e)}",
                )
            )

    return resultados_por_fuente

