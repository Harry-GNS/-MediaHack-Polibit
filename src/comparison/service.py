"""Comparación determinista y trazable de propuestas municipales."""
from __future__ import annotations

import unicodedata
from collections import defaultdict


_AMBITOS: dict[str, tuple[str, ...]] = {
    "Educación": ("educación", "educacion", "escuela", "colegio", "estudiante", "docente"),
    "Seguridad y convivencia": ("seguridad", "delincuencia", "violencia", "policía", "policia", "cámara", "camara"),
    "Movilidad": ("movilidad", "transporte", "metro", "buses", "vial", "ciclovía", "ciclovia"),
    "Ambiente y territorio": ("ambiente", "ambiental", "residuo", "reciclaje", "verde", "quebrada", "territorio"),
    "Economía y empleo": ("empleo", "emprendimiento", "economía", "economia", "comercio", "producción", "produccion"),
    "Espacio público y cultura": ("espacio público", "espacio publico", "cultura", "parque", "deporte", "recreación", "recreacion"),
    "Servicios municipales": ("agua", "alcantarillado", "recolección", "recoleccion", "alumbrado", "saneamiento"),
    "Inclusión y protección social": ("inclusión", "inclusion", "discapacidad", "niñez", "ninez", "mujer", "derechos", "salud"),
}


def _normalizar(texto: object) -> str:
    texto = unicodedata.normalize("NFD", str(texto).casefold())
    return "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")


def ambito_de_promesa(promesa: dict[str, object]) -> str:
    """Asigna un ámbito visible usando sólo la categoría y texto disponibles."""
    texto = " ".join(str(promesa.get(campo, "")) for campo in ("categoria", "accion", "objeto", "texto_original"))
    normalizado = _normalizar(texto)
    for ambito, palabras in _AMBITOS.items():
        if any(_normalizar(palabra) in normalizado for palabra in palabras):
            return ambito
    categoria = str(promesa.get("categoria") or "").strip()
    if categoria and categoria.casefold() != "no_especificado":
        return categoria.capitalize()
    return "Otros compromisos municipales"


def _fila(promesa: dict[str, object]) -> dict[str, object]:
    return {
        "candidato": promesa.get("candidato", "Candidatura sin identificar"),
        # La tabla presenta la cita original, no un texto reconstruido por el
        # extractor ni una interpretación del sistema.
        "propuesta": str(promesa.get("texto_original") or "").strip(),
        "texto_original": promesa.get("texto_original", ""),
        "pagina_o_seccion": promesa.get("pagina_o_seccion", "No especificada"),
        "enlace_documento": promesa.get("enlace_documento"),
    }


def comparar_promesas(promesas: list[dict[str, object]], candidato_ids: list[str]) -> dict[str, list[dict[str, object]]]:
    """Agrupa evidencia por ámbito, sin inferir que dos propuestas son iguales."""
    seleccionadas = set(candidato_ids)
    por_ambito: dict[str, dict[str, list[dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    for promesa in promesas:
        candidato = str(promesa.get("candidato", ""))
        if candidato in seleccionadas:
            por_ambito[ambito_de_promesa(promesa)][candidato].append(_fila(promesa))

    similitudes: list[dict[str, object]] = []
    diferencias: list[dict[str, object]] = []
    for ambito, por_candidato in sorted(por_ambito.items()):
        grupo = {
            "ambito": ambito,
            "propuestas_por_candidato": [
                {"candidato": candidato, "propuestas": propuestas}
                for candidato, propuestas in sorted(por_candidato.items())
            ],
        }
        (similitudes if len(por_candidato) >= 2 else diferencias).append(grupo)
    return {"similitudes": similitudes, "diferencias": diferencias}
