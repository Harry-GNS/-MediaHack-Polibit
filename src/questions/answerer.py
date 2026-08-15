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


def _terminos(texto: str) -> set[str]:
    return {
        termino for termino in re.findall(r"[a-záéíóúñü]{3,}", texto.casefold())
        if termino not in _PALABRAS_VACIAS
    }


def seleccionar_evidencias(pregunta: str, promesas: list[dict[str, object]], limite: int = 8) -> list[dict[str, object]]:
    """Ranking determinista simple para no enviar toda la base a la IA."""
    consulta = _terminos(pregunta)

    def puntaje(promesa: dict[str, object]) -> tuple[int, str]:
        texto = " ".join(str(promesa.get(campo, "")) for campo in ("categoria", "accion", "objeto", "texto_original"))
        return len(consulta & _terminos(texto)), str(promesa.get("id", ""))

    ordenadas = sorted(promesas, key=puntaje, reverse=True)
    relevantes = [promesa for promesa in ordenadas if puntaje(promesa)[0] > 0]
    return (relevantes or ordenadas)[:limite]


def responder_pregunta(pregunta: str, promesas: list[dict[str, object]]) -> tuple[str, list[dict[str, object]]]:
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
