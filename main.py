"""Script de demo: corre el flujo completo sobre un PDF de plan de gobierno.

    python main.py --pdf data/raw/plan_candidato_a.pdf --candidato-id cand_a \
        --candidato-nombre "Candidato A"

Pensado para probarse en vivo durante el hackathon: cada paso imprime lo
que va haciendo, para poder mostrar el flujo a alguien (por ejemplo, al
periodista con el que van a hablar) sin tener el frontend listo todavía.
"""
from __future__ import annotations

import argparse

from src.calculations.metrics import calcular_todos
from src.extraction.ai_structurer import estructurar_documento
from src.extraction.segmenter import segmentar_documento
from src.ingest.pdf_loader import extraer_texto_por_pagina
from src.models.schema import Candidato
from src.storage.db import guardar_candidato, guardar_promesa, inicializar_db
from src.validation.validators import validar_promesa


def correr_flujo(ruta_pdf: str, candidato_id: str, candidato_nombre: str) -> None:
    inicializar_db()

    candidato = Candidato(id=candidato_id, nombre=candidato_nombre, plan_gobierno_url=ruta_pdf)
    guardar_candidato(candidato)
    print(f"[1/6] Candidato registrado: {candidato_nombre}")

    paginas = extraer_texto_por_pagina(ruta_pdf)
    print(f"[2/6] PDF procesado: {len(paginas)} páginas extraídas")

    fragmentos = segmentar_documento(paginas)
    print(f"[3/6] Fragmentos candidatos a promesa encontrados: {len(fragmentos)}")

    promesas = estructurar_documento(fragmentos, candidato_id, ruta_pdf)
    print(f"[4/6] Promesas estructuradas por IA: {len(promesas)}")

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
    print("[6/6] Listo. Corre `uvicorn src.api.main:app --reload` para consultar la API.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Corre el flujo de Evidencia Electoral sobre un PDF.")
    parser.add_argument("--pdf", required=True, help="Ruta al PDF del plan de gobierno")
    parser.add_argument("--candidato-id", required=True, help="ID corto y único del candidato, p.ej. cand_a")
    parser.add_argument("--candidato-nombre", required=True, help="Nombre a mostrar del candidato")
    args = parser.parse_args()

    correr_flujo(args.pdf, args.candidato_id, args.candidato_nombre)
