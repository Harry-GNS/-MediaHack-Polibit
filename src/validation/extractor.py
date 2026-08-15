"""
src/validation/extractor.py
Extrae datos estadísticos/numéricos de un texto usando expresiones regulares.
"""
import re
from typing import Optional
from pydantic import BaseModel


class DatoEstadistico(BaseModel):
    texto_original: str       # Fragmento completo donde aparece el dato
    valor: float              # Valor numérico extraído
    unidad: str               # "%", "millones", "mil", "puntos", etc.
    contexto: str             # Texto circundante para dar semántica al dato


# Patrones en orden de especificidad (del más específico al más general)
_PATRONES: list[tuple[str, str]] = [
    # "tasa de desempleo del 4.7%", "índice de pobreza de 25.3%"
    (r'(?:tasa|índice|porcentaje|ratio)\s+de\s+[\w\s]+(?:del?|es?|fue)\s+(\d+(?:[.,]\d+)?)\s*(%|por\s*ciento)', "%"),
    # "40% de los hogares", "creció un 12.3%", "el 3.5 %"
    (r'(\d+(?:[.,]\d+)?)\s*(%|por\s*ciento)', "%"),
    # "3.2 millones de personas", "15 mil empleos"
    (r'(\d+(?:[.,]\d+)?)\s*(millones?|miles?|mil)\s+(?:de\s+)?[\w]+', "millones/mil"),
    # "incrementó en 15 puntos", "bajó 8 puntos porcentuales"
    (r'(\d+(?:[.,]\d+)?)\s*(puntos?(?:\s+porcentuales?)?)', "puntos"),
    # Números grandes con contexto: "1.200.000 personas"
    (r'(\d{1,3}(?:[.,]\d{3})+)\s+(personas?|hogares?|empleos?|trabajadores?|habitantes?)', "unidad"),
]

_WINDOW = 80   # caracteres de contexto a cada lado del dato


def _limpiar_numero(s: str) -> float:
    """Convierte strings como '3.200,5' o '3,200.5' a float."""
    s = s.strip()
    # Formato europeo: "3.200,5" → eliminar puntos y reemplazar coma
    if re.search(r'\d{1,3}(\.\d{3})+,\d+', s):
        s = s.replace(".", "").replace(",", ".")
    # Formato con coma de miles: "3,200.5"
    elif re.search(r'\d{1,3}(,\d{3})+', s):
        s = s.replace(",", "")
    # Coma decimal simple: "3,5" → "3.5"
    else:
        s = s.replace(",", ".")
    return float(s)


def extraer_datos_estadisticos(texto: str) -> list[DatoEstadistico]:
    """
    Extrae todos los datos estadísticos/numéricos detectables en el texto.

    Args:
        texto: El texto a analizar.

    Returns:
        Lista de DatoEstadistico, sin duplicados por posición.
    """
    datos: list[DatoEstadistico] = []
    posiciones_usadas: set[int] = set()
    texto_lower = texto.lower()

    for patron, unidad_default in _PATRONES:
        for match in re.finditer(patron, texto_lower, re.IGNORECASE):
            inicio = match.start()

            # Evitar extraer el mismo fragmento dos veces
            if any(abs(inicio - p) < 15 for p in posiciones_usadas):
                continue
            posiciones_usadas.add(inicio)

            # Extraer el número del primer grupo de captura
            try:
                valor_str = match.group(1).strip()
                valor = _limpiar_numero(valor_str)
            except (IndexError, ValueError):
                continue

            # Determinar unidad
            try:
                unidad_capturada = match.group(2).strip()
                unidad = "%" if "%" in unidad_capturada or "ciento" in unidad_capturada else unidad_capturada
            except IndexError:
                unidad = unidad_default

            # Extraer contexto (ventana de caracteres alrededor del match)
            start_ctx = max(0, inicio - _WINDOW)
            end_ctx = min(len(texto), match.end() + _WINDOW)
            contexto = texto[start_ctx:end_ctx].strip()
            texto_original = texto[inicio:match.end()].strip()

            datos.append(DatoEstadistico(
                texto_original=texto_original,
                valor=valor,
                unidad=unidad,
                contexto=contexto,
            ))

    return datos
