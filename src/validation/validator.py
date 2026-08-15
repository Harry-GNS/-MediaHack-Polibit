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
    "Si la fuente habla de la misma noticia, temática o evento, y la información es similar o parecida, debes marcarlo como 'concordante'. "
    "Si habla del mismo evento pero los datos contradicen directamente al usuario, pon 'discrepante'. "
    "Solo usa 'no_encontrado' si la fuente no tiene ABSOLUTAMENTE NADA que ver con el tema. "
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
  "valor_en_fuente": "<fragmento o dato de la fuente que se relaciona, o null si no se encuentra>",
  "explicacion": "<una oración neutral describiendo lo encontrado, sin veredictos>"
}}
""".strip()


class ResultadoValidacion(BaseModel):
    dato: DatoEstadistico
    estado: Literal["concordante", "discrepante", "no_encontrado"]
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


def validar_dato(
    dato: DatoEstadistico,
    fuentes_scrapeadas: list[dict],
) -> ResultadoValidacion:
    """
    Valida un dato estadístico contra la lista de fuentes scrapeadas.

    Itera por cada fuente y consulta OpenRouter. Si alguna fuente
    muestra concordancia, retorna inmediatamente. Si todas discrepan
    o no encuentran, retorna el peor resultado encontrado.

    Args:
        dato: El dato estadístico extraído del texto.
        fuentes_scrapeadas: Lista de resultados de scrapear_url().

    Returns:
        ResultadoValidacion con el estado final.
    """
    mejor_resultado: Optional[ResultadoValidacion] = None

    for fuente in fuentes_scrapeadas:
        if fuente.get("error"):
            continue  # Fuente no accesible, saltar

        # Construir texto de la fuente (permitir hasta 30000 chars ya que Gemini/Deepseek soportan mucho contexto)
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
            valor_fuente = respuesta.get("valor_en_fuente")
            explicacion = respuesta.get("explicacion", "Sin información adicional.")

            resultado = ResultadoValidacion(
                dato=dato,
                estado=estado,
                fuente_url=fuente["url"],
                valor_en_fuente=valor_fuente,
                alerta=explicacion,
            )

            # Si concordante, retornar inmediatamente (mejor caso)
            if estado == "concordante":
                return resultado

            # Guardar discrepante como candidato (mejor que no_encontrado)
            if mejor_resultado is None or (
                estado == "discrepante" and mejor_resultado.estado == "no_encontrado"
            ):
                mejor_resultado = resultado

        except (requests.RequestException, json.JSONDecodeError, KeyError):
            # Error en esta fuente: continuar con la siguiente
            continue

    # Si no hubo ningún resultado exitoso, retornar no_encontrado
    return mejor_resultado or ResultadoValidacion(
        dato=dato,
        estado="no_encontrado",
        fuente_url=None,
        valor_en_fuente=None,
        alerta="No se pudo verificar el dato en ninguna de las fuentes proporcionadas.",
    )


def validar_texto(texto: str, fuentes_scrapeadas: list[dict]) -> list[ResultadoValidacion]:
    """
    Pipeline completo: valida el texto completo contra las fuentes.
    
    Args:
        texto: El texto ingresado por el usuario.
        fuentes_scrapeadas: Lista de resultados de scrapear_url().

    Returns:
        Lista de ResultadoValidacion.
    """
    from src.validation.extractor import DatoEstadistico

    dato = DatoEstadistico(
        texto_original=texto,
        valor=0.0,
        unidad="",
        contexto="Validación de texto completo"
    )

    return [validar_dato(dato, fuentes_scrapeadas)]

