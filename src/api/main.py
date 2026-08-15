"""Endpoints que alimentan el selector de proceso electoral del frontend."""
from __future__ import annotations

from pathlib import Path
import logging
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, status
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
_TRABAJOS_PROCESAMIENTO: dict[str, dict[str, object]] = {}


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


def _ejecutar_procesamiento(
    trabajo_id: str, proceso_id: str, seleccionadas: list[object], max_fragmentos: int
) -> None:
    try:
        scraper = ScraperCNE()
        manifiesto = scraper.descargar_planes(proceso_id, seleccionadas)
        documentos = {documento["id"]: documento for documento in manifiesto["documentos"]}
        from main import correr_flujo

        for indice, candidatura in enumerate(seleccionadas, start=1):
            _TRABAJOS_PROCESAMIENTO[trabajo_id].update({
                "estado": "procesando",
                "mensaje": f"Procesando {candidatura.nombre} ({indice}/{len(seleccionadas)})…",
                "completadas": indice - 1,
            })
            ruta_pdf = Path(documentos[candidatura.id]["archivo_local"])
            correr_flujo(
                str(ruta_pdf),
                candidatura.id,
                candidatura.nombre,
                candidatura.proceso_electoral_id,
                candidatura.dignidad,
                candidatura.organizacion_politica,
                max_fragmentos,
            )
        _TRABAJOS_PROCESAMIENTO[trabajo_id].update({
            "estado": "completado",
            "mensaje": "Planes descargados y evidencia disponible para comparar.",
            "completadas": len(seleccionadas),
        })
    except Exception as error:
        logger.exception("Falló el procesamiento de planes del proceso %s", proceso_id)
        texto_error = str(error).casefold()
        if "credit" in texto_error or "error code: 402" in texto_error or "code': 402" in texto_error:
            mensaje = "OpenRouter no tiene saldo suficiente para este lote. Reduce el límite de salida o agrega créditos."
        else:
            mensaje = f"Falló el procesamiento del plan: {type(error).__name__}. Revisa la consola del servidor para el detalle."
        _TRABAJOS_PROCESAMIENTO[trabajo_id].update({
            "estado": "fallido",
            "mensaje": mensaje,
        })


@app.post("/procesos-electorales/{proceso_id}/procesar-planes", status_code=status.HTTP_202_ACCEPTED)
def procesar_planes(
    proceso_id: str, solicitud: ProcesarPlanesRequest, tareas: BackgroundTasks
) -> dict[str, object]:
    """Inicia un procesamiento en segundo plano y devuelve de inmediato."""
    try:
        disponibles = {candidatura.id: candidatura for candidatura in ScraperCNE().descubrir_candidaturas(proceso_id)}
    except CNEError as error:
        raise _error_cne(error) from error
    ausentes = sorted(set(solicitud.candidato_ids) - set(disponibles))
    if ausentes:
        raise HTTPException(status_code=404, detail={"candidaturas_no_encontradas": ausentes})
    seleccionadas = [disponibles[candidato_id] for candidato_id in solicitud.candidato_ids]
    trabajo_id = str(uuid4())
    _TRABAJOS_PROCESAMIENTO[trabajo_id] = {
        "estado": "en_cola",
        "mensaje": "Planificando descarga y extracción…",
        "completadas": 0,
        "total": len(seleccionadas),
    }
    tareas.add_task(_ejecutar_procesamiento, trabajo_id, proceso_id, seleccionadas, solicitud.max_fragmentos)
    return {"trabajo_id": trabajo_id, **_TRABAJOS_PROCESAMIENTO[trabajo_id]}


@app.get("/procesamientos/{trabajo_id}")
def estado_procesamiento(trabajo_id: str) -> dict[str, object]:
    try:
        return {"trabajo_id": trabajo_id, **_TRABAJOS_PROCESAMIENTO[trabajo_id]}
    except KeyError as error:
        raise HTTPException(status_code=404, detail="No existe ese procesamiento o el servidor se reinició.") from error
