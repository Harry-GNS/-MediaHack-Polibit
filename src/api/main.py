"""Endpoints que alimentan el selector de proceso electoral del frontend."""
from __future__ import annotations

from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.extraction.ai_structurer import ConfiguracionIAError
from src.comparison.service import comparar_promesas
from src.ingest.cne_scraper import CNEError, ScraperCNE, listar_procesos
from src.questions.answerer import responder_pregunta
from src.storage.db import listar_candidatos, obtener_promesas

_STATIC_DIR = Path(__file__).resolve().parent / "static"
app = FastAPI(title="Evidencia Municipal", version="0.2.0")
logger = logging.getLogger(__name__)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


class DescargaPlanesRequest(BaseModel):
    candidato_ids: list[str] = Field(min_length=1, max_length=5)


class ProcesarPlanesRequest(BaseModel):
    candidato_ids: list[str] = Field(min_length=1, max_length=2)
    max_fragmentos: int = Field(default=40, ge=10, le=120)


class PreguntaRequest(BaseModel):
    pregunta: str = Field(min_length=8, max_length=600)
    candidato_ids: list[str] = Field(default_factory=list, max_length=5)


class ComparacionRequest(BaseModel):
    candidato_ids: list[str] = Field(min_length=2, max_length=2)


def _error_cne(error: CNEError) -> HTTPException:
    return HTTPException(status_code=502, detail=str(error))


@app.get("/", include_in_schema=False)
def interfaz() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/candidatos")
def candidatos_cargados(
    proceso_electoral_id: str | None = None,
    canton: str | None = Query(default=None, min_length=2),
) -> list[dict[str, object]]:
    """Evidencia ya procesada, restringida al proceso y cantón de la vista."""
    candidatos = listar_candidatos()
    if proceso_electoral_id:
        candidatos = [c for c in candidatos if c.get("proceso_electoral_id") == proceso_electoral_id]
    if canton:
        termino = canton.casefold()
        candidatos = [
            candidato
            for candidato in candidatos
            if termino in str(candidato.get("dignidad") or "").casefold()
        ]
    return candidatos


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


@app.post("/comparaciones")
def comparar_planes(solicitud: ComparacionRequest) -> dict[str, object]:
    promesas = obtener_promesas(solicitud.candidato_ids)
    if not promesas:
        raise HTTPException(status_code=404, detail="No hay evidencia procesada para las candidaturas seleccionadas.")
    return comparar_promesas(promesas, solicitud.candidato_ids)


@app.get("/procesos-electorales")
def procesos_electorales() -> list[dict[str, object]]:
    """Opciones que el frontend muestra en el menú inicial."""
    return listar_procesos()


@app.get("/procesos-electorales/{proceso_id}/candidaturas")
def candidaturas_de_proceso(proceso_id: str, canton: str | None = Query(default=None, min_length=2)) -> list[dict[str, object]]:
    try:
        candidaturas = ScraperCNE().descubrir_candidaturas(proceso_id)
        if canton:
            termino = canton.casefold()
            candidaturas = [
                candidatura
                for candidatura in candidaturas
                if termino in (candidatura.territorio or candidatura.dignidad).casefold()
            ]
        return [candidatura.resumen() for candidatura in candidaturas]
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


@app.post("/procesos-electorales/{proceso_id}/procesar-planes")
def procesar_planes(proceso_id: str, solicitud: ProcesarPlanesRequest) -> dict[str, object]:
    """Descarga planes públicos seleccionados y los deja listos para comparar.

    Se limita a dos candidaturas y a una muestra explícita para que la acción
    de la interfaz sea apta para la demo; el CLI conserva el modo exhaustivo.
    """
    try:
        scraper = ScraperCNE()
        disponibles = {candidatura.id: candidatura for candidatura in scraper.descubrir_candidaturas(proceso_id)}
        ausentes = sorted(set(solicitud.candidato_ids) - set(disponibles))
        if ausentes:
            raise HTTPException(status_code=404, detail={"candidaturas_no_encontradas": ausentes})
        seleccionadas = [disponibles[candidato_id] for candidato_id in solicitud.candidato_ids]
        manifiesto = scraper.descargar_planes(proceso_id, seleccionadas)
        documentos = {documento["id"]: documento for documento in manifiesto["documentos"]}
        from main import correr_flujo

        for candidatura in seleccionadas:
            ruta_pdf = Path(documentos[candidatura.id]["archivo_local"])
            correr_flujo(
                str(ruta_pdf),
                candidatura.id,
                candidatura.nombre,
                candidatura.proceso_electoral_id,
                candidatura.dignidad,
                candidatura.organizacion_politica,
                solicitud.max_fragmentos,
            )
        return {
            "procesadas": [candidatura.resumen() for candidatura in seleccionadas],
            "max_fragmentos": solicitud.max_fragmentos,
            "mensaje": "Planes descargados y evidencia disponible para comparar.",
        }
    except CNEError as error:
        raise _error_cne(error) from error
    except ConfiguracionIAError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        # Normalmente indica JSON inválido del modelo: se reporta al usuario
        # para que pueda reintentar sin un 500 opaco.
        raise HTTPException(status_code=422, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Falló el procesamiento de planes del proceso %s", proceso_id)
        raise HTTPException(
            status_code=502,
            detail=f"Falló el procesamiento del plan: {type(error).__name__}: {error}",
        ) from error
