"""Endpoints que alimentan el selector de proceso electoral del frontend."""
from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.extraction.ai_structurer import ConfiguracionIAError
from src.ingest.cne_scraper import CNEError, ScraperCNE, listar_procesos
from src.questions.answerer import responder_pregunta
from src.storage.db import listar_candidatos, obtener_promesas
from src.validation.validator import validar_texto
from app import scrapear_url

_STATIC_DIR = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Evidencia Municipal", version="0.2.0")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Habilitar CORS para el frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DescargaPlanesRequest(BaseModel):
    candidato_ids: list[str] = Field(min_length=1, max_length=5)


class ValidarRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=8000, description="Texto a validar")
    fuentes: List[str] = Field(min_length=1, max_length=10, description="Lista de URLs de fuentes confiables")


class PreguntaRequest(BaseModel):
    pregunta: str = Field(min_length=8, max_length=600)
    candidato_ids: list[str] = Field(default_factory=list, max_length=5)


def _error_cne(error: CNEError) -> HTTPException:
    return HTTPException(status_code=502, detail=str(error))


@app.get("/", include_in_schema=False)
def interfaz() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/candidatos")
def candidatos_cargados() -> list[dict[str, object]]:
    return listar_candidatos()


@app.get("/candidatos/{candidato_id}/promesas")
def promesas_de_candidato(candidato_id: str) -> list[dict[str, object]]:
    promesas = obtener_promesas([candidato_id])
    if not promesas:
        raise HTTPException(status_code=404, detail="No hay promesas procesadas para este candidato.")
    return promesas


@app.post("/preguntas")
def preguntas_de_planes(solicitud: PreguntaRequest) -> dict[str, object]:
    promesas = obtener_promesas(solicitud.candidato_ids or None)
    if not promesas:
        raise HTTPException(status_code=404, detail="No hay planes procesados para la selección actual.")
    try:
        respuesta, evidencias = responder_pregunta(solicitud.pregunta, promesas)
    except ConfiguracionIAError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"respuesta": respuesta, "evidencias": evidencias}


@app.post("/validar")
def validar_datos(solicitud: ValidarRequest) -> list[dict]:
    """
    Extrae datos estadísticos del texto y los valida contra las fuentes proporcionadas.
    Principio: 'Sin veredictos, solo evidencia'.
    """
    # 1. Scrapear todas las fuentes
    fuentes_scrapeadas = [scrapear_url(url) for url in solicitud.fuentes]

    # 2. Validar el texto contra las fuentes
    resultados = validar_texto(solicitud.texto, fuentes_scrapeadas)

    if not resultados:
        raise HTTPException(
            status_code=422,
            detail="No se detectaron datos estadísticos o numéricos en el texto proporcionado."
        )

    return [r.model_dump() for r in resultados]


@app.get("/procesos-electorales")
def procesos_electorales() -> list[dict[str, object]]:
    """Opciones que el frontend muestra en el menú inicial."""
    return listar_procesos()


@app.get("/procesos-electorales/{proceso_id}/candidaturas")
def candidaturas_de_proceso(proceso_id: str) -> list[dict[str, object]]:
    try:
        return [candidatura.resumen() for candidatura in ScraperCNE().descubrir_candidaturas(proceso_id)]
    except CNEError as error:
        raise _error_cne(error) from error


@app.post("/procesos-electorales/{proceso_id}/descargar-planes")
def descargar_planes(proceso_id: str, solicitud: DescargaPlanesRequest) -> dict[str, object]:
    try:
        scraper = ScraperCNE()
        disponibles = {candidatura.id: candidatura for candidatura in scraper.descubrir_candidaturas(proceso_id)}
        ausentes = sorted(set(solicitud.candidato_ids) - set(disponibles))
        if ausentes:
            raise HTTPException(status_code=404, detail={"candidaturas_no_encontradas": ausentes})
        seleccionadas = [disponibles[candidato_id] for candidato_id in solicitud.candidato_ids]
        return scraper.descargar_planes(proceso_id, seleccionadas)
    except CNEError as error:
        raise _error_cne(error) from error
