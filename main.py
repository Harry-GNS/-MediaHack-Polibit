"""Script de demo: corre el flujo completo sobre un PDF de plan de gobierno.

    python main.py --pdf data/raw/plan_candidato_a.pdf --candidato-id cand_a \
        --candidato-nombre "Candidato A"

Pensado para probarse en vivo durante el hackathon: cada paso imprime lo
que va haciendo, para poder mostrar el flujo a alguien (por ejemplo, al
periodista con el que van a hablar) sin tener el frontend listo todavía.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.calculations.metrics import calcular_todos
from src.extraction.ai_structurer import estructurar_documento, estructurar_documento_local
from src.extraction.segmenter import segmentar_documento
from src.ingest.pdf_loader import extraer_texto_por_pagina
from src.ingest.cne_scraper import CNEError, ScraperCNE
from src.models.schema import Candidato
from src.storage.db import guardar_candidato, guardar_promesa, inicializar_db
from src.validation.validators import validar_promesa


def correr_flujo(
    ruta_pdf: str,
    candidato_id: str,
    candidato_nombre: str,
    proceso_electoral_id: str | None = None,
    dignidad: str | None = None,
    organizacion_politica: str | None = None,
    max_fragmentos: int | None = None,
    usar_ia: bool = False,
    plan_gobierno_url: str | None = None,
) -> None:
    # Validar el documento antes de modificar la base de datos. Así una ruta
    # escrita como ejemplo no deja una candidatura sin evidencia asociada.
    paginas = extraer_texto_por_pagina(ruta_pdf)
    inicializar_db()

    candidato = Candidato(
        id=candidato_id,
        nombre=candidato_nombre,
        # Para documentos obtenidos del catálogo se conserva la URL pública;
        # la ruta local sólo sirve a la extracción. Así la evidencia puede
        # llevar de vuelta al PDF verificable en el navegador.
        plan_gobierno_url=plan_gobierno_url or ruta_pdf,
        proceso_electoral_id=proceso_electoral_id,
        dignidad=dignidad,
        organizacion_politica=organizacion_politica,
    )
    guardar_candidato(candidato)
    print(f"[1/6] Candidato registrado: {candidato_nombre}")

    print(f"[2/6] PDF procesado: {len(paginas)} páginas extraídas")

    fragmentos = segmentar_documento(paginas)
    print(f"[3/6] Fragmentos candidatos a promesa encontrados: {len(fragmentos)}")

    if usar_ia:
        promesas = estructurar_documento(fragmentos, candidato_id, ruta_pdf, max_fragmentos=max_fragmentos)
        print(f"[4/6] Promesas estructuradas por IA: {len(promesas)}")
    else:
        promesas = estructurar_documento_local(fragmentos, candidato_id, ruta_pdf, max_fragmentos=max_fragmentos)
        print(f"[4/6] Evidencia estructurada localmente (0 tokens): {len(promesas)}")

    guardadas = 0
    for promesa in promesas:
        resultado = validar_promesa(promesa)
        if not resultado.valida:
            print(f"  ✗ Promesa descartada por validación: {resultado.errores}")
            continue
        if resultado.advertencias:
            print(f"  ⚠ {promesa.accion} {promesa.objeto}: {resultado.advertencias}")

        # NOTA: el cruce con datos históricos (src/matching/crosser.py) se
        # omite en este demo mínimo porque depende de tener datasets
        # cargados en data/historical/. Ver README para cómo conectarlo.
        promesa.calculos = calcular_todos(promesa, anios_plazo=None)

        guardar_promesa(promesa)
        guardadas += 1

    print(f"[5/6] Promesas guardadas en base de datos: {guardadas}")
    print("[6/6] Listo. Corre `python -m uvicorn src.api.main:app --reload` para consultar la API.")


def descargar_plan_cne(proceso_id: str, candidatura_id: str) -> tuple[str, object]:
    """Descarga una candidatura publicada por CNE y devuelve su PDF local."""
    scraper = ScraperCNE()
    disponibles = {candidatura.id: candidatura for candidatura in scraper.descubrir_candidaturas(proceso_id)}
    try:
        candidatura = disponibles[candidatura_id]
    except KeyError as exc:
        raise ValueError(f"La candidatura no fue publicada para {proceso_id}: {candidatura_id}") from exc
    manifiesto = scraper.descargar_planes(proceso_id, [candidatura])
    documento = next(documento for documento in manifiesto["documentos"] if documento["id"] == candidatura_id)
    # El manifiesto usa una ruta relativa al repositorio (data/raw/...).
    return str(Path(documento["archivo_local"])), candidatura


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corre el flujo de Evidencia Electoral sobre un PDF.")
    origen = parser.add_mutually_exclusive_group(required=True)
    origen.add_argument("--pdf", help="Ruta existente al PDF oficial del plan de gobierno")
    origen.add_argument("--cne-candidatura-id", help="ID descubierto y descargado desde el CNE")
    parser.add_argument("--cne-proceso-id", help="Proceso CNE del que se descargará la candidatura")
    parser.add_argument("--candidato-id", help="ID corto y único del candidato, p.ej. cand_a")
    parser.add_argument("--candidato-nombre", help="Nombre a mostrar del candidato")
    parser.add_argument("--proceso-electoral-id", help="Identificador del proceso, p.ej. seccionales_2027")
    parser.add_argument("--dignidad", help="Dignidad electoral, p.ej. Alcaldía de Quito")
    parser.add_argument("--organizacion-politica", help="Organización política que consta en el documento oficial")
    parser.add_argument(
        "--max-fragmentos",
        type=int,
        help="Modo rápido: máximo de fragmentos a enviar a IA; usa una muestra distribuida por el documento.",
    )
    parser.add_argument("--usar-ia", action="store_true", help="Usa OpenRouter para estructuración avanzada; consume tokens.")
    args = parser.parse_args()

    try:
        if args.cne_candidatura_id:
            if not args.cne_proceso_id:
                parser.error("--cne-proceso-id es obligatorio al usar --cne-candidatura-id")
            ruta_pdf, candidatura = descargar_plan_cne(args.cne_proceso_id, args.cne_candidatura_id)
            candidato_id = args.candidato_id or candidatura.id
            candidato_nombre = args.candidato_nombre or candidatura.nombre
            proceso_electoral_id = args.proceso_electoral_id or candidatura.proceso_electoral_id
            dignidad = args.dignidad or candidatura.dignidad
            organizacion_politica = args.organizacion_politica or candidatura.organizacion_politica
            print(f"[0/6] Plan descargado desde CNE: {ruta_pdf}")
        else:
            if not args.candidato_id or not args.candidato_nombre:
                parser.error("--candidato-id y --candidato-nombre son obligatorios al usar --pdf")
            ruta_pdf = args.pdf
            candidato_id = args.candidato_id
            candidato_nombre = args.candidato_nombre
            proceso_electoral_id = args.proceso_electoral_id
            dignidad = args.dignidad
            organizacion_politica = args.organizacion_politica
        correr_flujo(
            ruta_pdf,
            candidato_id,
            candidato_nombre,
            proceso_electoral_id,
            dignidad,
            organizacion_politica,
            args.max_fragmentos,
            args.usar_ia,
            candidatura.plan_url if args.cne_candidatura_id else None,
        )
    except (CNEError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))
