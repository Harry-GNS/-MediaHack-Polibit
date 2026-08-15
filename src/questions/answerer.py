"""Pregunta-respuesta acotada a planes procesados y sus páginas fuente."""
from __future__ import annotations

import re
from typing import Any

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


def _respuesta_local(evidencias: list[dict[str, object]]) -> str:
    """Mensaje de cabecera para un RAG estrictamente extractivo."""
    return "Fragmentos textuales recuperados del plan de trabajo. Consulta el PDF fuente enlazado en cada fila."


def responder_pregunta(pregunta: str, promesas: list[dict[str, object]]) -> tuple[str, list[dict[str, object]]]:
    if not pregunta_permitida(pregunta, promesas):
        return _MENSAJE_PREGUNTA_NO_PERMITIDA, []
    evidencias = seleccionar_evidencias(pregunta, promesas)
    if not evidencias:
        raise ValueError("No hay promesas procesadas para responder la pregunta.")
    # El producto es un RAG extractivo: esta función nunca envía la pregunta,
    # ni el contenido del plan, a un proveedor de IA. La interfaz presenta
    # exactamente ``texto_original`` desde ``evidencias``.
    return _respuesta_local(evidencias), evidencias
