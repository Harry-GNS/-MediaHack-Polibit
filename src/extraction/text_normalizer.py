"""Normalización conservadora de texto extraído de PDFs.

No resume ni corrige el contenido político: sólo normaliza espacios y evita
mostrar fragmentos cuya codificación/orden de glifos no permita una lectura
responsable. El PDF fuente siempre permanece disponible como evidencia.
"""
from __future__ import annotations

import re
import unicodedata


_PALABRAS = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
_SERIE_LETRAS_SUELTAS = re.compile(r"(?:\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]\b\s+){4,}")


def estandarizar_texto(texto: object) -> str:
    """Unifica Unicode, espacios y cortes de línea sin alterar las palabras."""
    texto = unicodedata.normalize("NFC", str(texto or "")).replace("\u00a0", " ")
    # Sólo se unen palabras rotas inequívocamente por un salto de línea.
    texto = re.sub(r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])-\s*\n\s*(?=[a-záéíóúüñ])", "", texto)
    lineas = [re.sub(r"[ \t]+", " ", linea).strip() for linea in texto.splitlines()]
    return "\n".join(linea for linea in lineas if linea)


def es_texto_presentable(texto: object) -> bool:
    """Determina si un fragmento puede presentarse como cita textual.

    Un bloque con muchas letras aisladas suele provenir de una tabla PDF con
    orden de glifos corrupto. Ocultarlo es preferible a atribuir una frase sin
    sentido a una candidatura.
    """
    normalizado = estandarizar_texto(texto)
    palabras = _PALABRAS.findall(normalizado)
    if len(normalizado) < 24 or len(palabras) < 4:
        return False
    if _SERIE_LETRAS_SUELTAS.search(normalizado):
        return False
    proporcion_cortas = sum(len(palabra) <= 2 for palabra in palabras) / len(palabras)
    return proporcion_cortas <= 0.30


def evidencia_estandarizada(promesa: dict[str, object]) -> dict[str, object] | None:
    """Devuelve una copia presentable o ``None`` si la cita no es fiable."""
    texto = estandarizar_texto(promesa.get("texto_original"))
    if not es_texto_presentable(texto):
        return None
    resultado = dict(promesa)
    resultado["texto_original"] = texto
    return resultado
