"""Pregunta-respuesta acotada a planes procesados y sus páginas fuente."""
from __future__ import annotations

import re
from typing import Any

from config import OPENROUTER_MODEL
from src.extraction.ai_structurer import ConfiguracionIAError, _cliente_por_defecto

_PALABRAS_VACIAS = {
    "para", "sobre", "entre", "desde", "hasta", "como", "cuál", "cuales", "que", "qué",
    "plan", "planes", "trabajo", "candidato", "candidatos", "propuesta", "propuestas",
    "con", "por", "del", "las", "los", "una", "uno", "sus", "hay", "son", "se",
}

_MENSAJE_PREGUNTA_NO_PERMITIDA = "Por favor, realice una pregunta relacionada con los planes de trabajo."
_PATRONES_RIESGO = (
    "ignore", "ignora", "olvida", "disregard", "system prompt", "prompt del sistema", "prompt",
    "instrucciones", "instruction", "api key", "api_key", "openrouter", "contraseña", "password",
    "revela", "reveal", "secreto", "secret", "jailbreak", "roleplay", "actua como", "actúa como",
    "bypass", "```", "<script", "</", "http://", "https://",
)
_ANCLAS_PLAN = {
    "plan", "planes", "propuesta", "propuestas", "promesa", "promesas", "candidato", "candidatos",
    "candidatura", "candidaturas", "comparar", "comparacion", "diferencia", "diferencias", "similar",
    "similares", "alcaldia", "canton", "municipal", "propone", "proponen", "plantea", "plantean",
    "ofrece", "ofrecen", "compromiso", "compromisos",
}


def _terminos(texto: str) -> set[str]:
    return {
        termino for termino in re.findall(r"[a-záéíóúñü]{3,}", texto.casefold())
        if termino not in _PALABRAS_VACIAS
    }


def seleccionar_evidencias(pregunta: str, promesas: list[dict[str, object]], limite: int = 8) -> list[dict[str, object]]:
    """Ranking determinista simple para no enviar toda la base a la IA."""
    consulta = _terminos(pregunta)

    def puntaje(promesa: dict[str, object]) -> tuple[int, str]:
        texto = " ".join(str(promesa.get(campo, "")) for campo in ("candidato", "categoria", "accion", "objeto", "texto_original"))
        return len(consulta & _terminos(texto)), str(promesa.get("id", ""))

    ordenadas = sorted(promesas, key=puntaje, reverse=True)
    relevantes = [promesa for promesa in ordenadas if puntaje(promesa)[0] > 0]
    return (relevantes or ordenadas)[:limite]


def pregunta_permitida(pregunta: str, promesas: list[dict[str, object]]) -> bool:
    """Filtro local: una pregunta no permitida nunca llega al proveedor IA."""
    normalizada = pregunta.casefold().strip()
    if not normalizada or len(normalizada) > 600 or any(patron in normalizada for patron in _PATRONES_RIESGO):
        return False
    terminos = _terminos(pregunta)
    if terminos & _ANCLAS_PLAN:
        return True
    terminos_evidencia: set[str] = set()
    for promesa in promesas:
        texto = " ".join(str(promesa.get(campo, "")) for campo in ("categoria", "accion", "objeto", "texto_original"))
        terminos_evidencia.update(_terminos(texto))
    return bool(terminos & terminos_evidencia)


def responder_pregunta(pregunta: str, promesas: list[dict[str, object]]) -> tuple[str, list[dict[str, object]]]:
    if not pregunta_permitida(pregunta, promesas):
        return _MENSAJE_PREGUNTA_NO_PERMITIDA, []
    evidencias = seleccionar_evidencias(pregunta, promesas)
    if not evidencias:
        raise ValueError("No hay promesas procesadas para responder la pregunta.")
    contexto = "\n\n".join(
        f"[E{indice}] Candidato: {promesa.get('candidato')}; página: {promesa.get('pagina_o_seccion')}; "
        f"acción: {promesa.get('accion')}; objeto: {promesa.get('objeto')}; texto: {promesa.get('texto_original')}"
        for indice, promesa in enumerate(evidencias, start=1)
    )
    sistema = """Responde únicamente con la evidencia de planes de trabajo proporcionada.
No determines viabilidad, veracidad, calidad ni recomiendes candidatos. Si la evidencia no basta,
indícalo claramente. Distingue entre lo que dice cada candidato y cita las referencias [E1], [E2].
Mantén el enfoque de gobierno municipal: alcaldías, concejos, cantones y servicios locales cuando
la evidencia lo permita."""
    cliente = _cliente_por_defecto()
    respuesta = cliente.chat.completions.create(
        model=OPENROUTER_MODEL,
        temperature=0,
        max_tokens=700,
        messages=[
            {"role": "system", "content": sistema},
            {"role": "user", "content": f"Pregunta: {pregunta}\n\nEvidencia:\n{contexto}"},
        ],
    )
    texto = respuesta.choices[0].message.content
    if not texto:
        raise ConfiguracionIAError("OpenRouter no devolvió texto para la pregunta.")
    return texto, evidencias
