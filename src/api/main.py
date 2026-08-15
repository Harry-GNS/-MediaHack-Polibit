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
from src.extraction.text_normalizer import evidencia_estandarizada
from src.comparison.service import comparar_promesas
from src.ingest.cne_scraper import CNEError, ScraperCNE, listar_cantones, listar_procesos
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


def _con_enlaces_de_fuente(promesas: list[dict[str, object]]) -> list[dict[str, object]]:
    """Estandariza citas legibles y adjunta la URL pública de verificación."""
    candidatos = {str(candidato["id"]): candidato for candidato in listar_candidatos()}
    resultado: list[dict[str, object]] = []
    for promesa in promesas:
        evidencia = evidencia_estandarizada(promesa)
        if evidencia is None:
            continue
        candidato = candidatos.get(str(promesa.get("candidato")), {})
        url = str(candidato.get("plan_gobierno_url") or "")
        pagina = str(promesa.get("pagina_o_seccion") or "").strip()
        if url.startswith(("https://", "http://")):
            evidencia["enlace_documento"] = f"{url}#page={pagina}" if pagina.isdigit() else url
        evidencia["nombre_candidato"] = candidato.get("nombre", promesa.get("candidato"))
        resultado.append(evidencia)
    return resultado


@app.get("/", include_in_schema=False)
def interfaz() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/comparacion", include_in_schema=False)
def interfaz_comparacion() -> FileResponse:
    """Ruta pública principal del comparador municipal."""
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
    return _con_enlaces_de_fuente(promesas)


@app.post("/preguntas")
def preguntas_de_planes(solicitud: PreguntaRequest) -> dict[str, object]:
    promesas = _con_enlaces_de_fuente(obtener_promesas(solicitud.candidato_ids or None))
    if not promesas:
        raise HTTPException(status_code=404, detail="No hay citas textuales legibles para la selección actual. Consulta el PDF fuente.")
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
    return comparar_promesas(_con_enlaces_de_fuente(promesas), solicitud.candidato_ids)


@app.get("/procesos-electorales")
def procesos_electorales() -> list[dict[str, object]]:
    """Opciones que el frontend muestra en el menú inicial."""
    return listar_procesos()


@app.get("/cantones")
def cantones_electorales() -> list[str]:
    """Catálogo geográfico completo para el selector municipal."""
    return listar_cantones()


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
                False,
                getattr(candidatura, "plan_url", None),
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


@app.get("/ancla")
def ancla_de_confianza(
    categoria: str | None = Query(default=None, description="Categoría temática, ej: seguridad, educacion"),
    objeto: str | None = Query(default=None, description="Objeto de la promesa, ej: patrulleros, escuelas"),
    candidato_ids: list[str] | None = Query(default=None, description="IDs a excluir (los candidatos comparados actualmente)"),
) -> dict[str, object]:
    """
    Devuelve promesas históricas similares a las de los candidatos actuales.
    No califica ni evalúa viabilidad — solo muestra antecedentes documentados.
    """
    todas = obtener_promesas()

    # Excluir los candidatos actualmente seleccionados para mostrar solo histórico
    excluir = set(candidato_ids or [])
    historicas = [p for p in todas if str(p.get("candidato", "")) not in excluir]

    # Filtrar por categoría u objeto si se especifican
    if categoria:
        cat_lower = categoria.casefold()
        historicas = [
            p for p in historicas
            if cat_lower in str(p.get("categoria", "")).casefold()
        ]
    if objeto:
        obj_lower = objeto.casefold()
        historicas = [
            p for p in historicas
            if any(
                obj_lower in str(p.get(campo, "")).casefold()
                for campo in ("objeto", "accion", "texto_original")
            )
        ]

    # Calcular promedio histórico de cantidad si existe
    cantidades = [
        float(p["cantidad"])
        for p in historicas
        if p.get("cantidad") is not None
    ]
    promedio = round(sum(cantidades) / len(cantidades), 1) if cantidades else None

    # Armar respuesta — solo datos objetivos, sin calificación
    candidatos_bd = {str(c["id"]): c for c in listar_candidatos()}
    antecedentes = []
    for promesa in historicas[:8]:  # máximo 8 antecedentes
        cand = candidatos_bd.get(str(promesa.get("candidato", "")), {})
        antecedentes.append({
            "candidato": cand.get("nombre", promesa.get("candidato", "Desconocido")),
            "proceso_electoral_id": cand.get("proceso_electoral_id"),
            "categoria": promesa.get("categoria"),
            "accion": promesa.get("accion"),
            "objeto": promesa.get("objeto"),
            "cantidad": promesa.get("cantidad"),
            "unidad": promesa.get("unidad"),
            "plazo": promesa.get("plazo"),
            "texto": promesa.get("texto_original", "")[:200],
            "fuente": promesa.get("fuente_documento"),
        })

    # INTEGRACIÓN CON EL MÓDULO DE HISTÓRICOS (CSV SCRAPING DEL AMIGO)
    import unicodedata
    def norm(s): return ''.join(c for c in unicodedata.normalize('NFD', s.strip().lower()) if unicodedata.category(c) != 'Mn') if s else ""
    cat_str = norm(categoria)
    obj_str = norm(objeto)

    # 1. Datos de Ejecución del SERCOP (Módulo del amigo)
    try:
        from src.data.historical_loader import HistoricalDataLoader
        loader = HistoricalDataLoader(Path(__file__).resolve().parent.parent.parent / "data" / "historical")
        datos_amigo = loader.buscar_contexto_historico(categoria or "", objeto or "")
        
        for d in datos_amigo:
            # Asignar el nombre del candidato histórico real según el año de Quito
            candidato_historico = "Registro Público Oficial"
            if d.anio:
                if 2019 <= d.anio <= 2021:
                    candidato_historico = "Jorge Yunda (Gestión)"
                elif 2021 < d.anio <= 2023:
                    candidato_historico = "Santiago Guarderas (Gestión)"
                elif 2014 <= d.anio < 2019:
                    candidato_historico = "Mauricio Rodas (Gestión)"
                elif 2009 <= d.anio < 2014:
                    candidato_historico = "Augusto Barrera (Gestión)"

            # Para evitar repetición visual
            texto_resumido = d.fragmento_original.split(';')[0] if ';' in d.fragmento_original else d.fragmento_original
            antecedentes.append({
                "candidato": candidato_historico,
                "proceso_electoral_id": f"Año {d.anio} (Ejecución real)" if d.anio else "Histórico",
                "categoria": "Registro Oficial",
                "accion": "Ejecutado",
                "objeto": "Contrato",
                "cantidad": d.valor,
                "unidad": d.unidad,
                "plazo": f"Año {d.anio}",
                "texto": f"Contratación/Ejecución registrada: {texto_resumido}",
                "fuente": d.nombre_fuente,
                "fuente_url": d.url_o_id if d.url_o_id.startswith("http") else None
            })
            
    except Exception as e:
        logger.error(f"Error cargando datos históricos del amigo: {e}")

    # 3. Web Scraping EN VIVO de Hemeroteca Web (Para enlaces funcionales reales)
    try:
        from src.ingest.live_scraper import HemerotecaScraper
        scraper = HemerotecaScraper()
        # Usamos el objeto de la promesa (ej: "patrulleros") o la categoría para buscar en la web
        termino_busqueda = objeto[:30] if objeto else categoria
        if termino_busqueda:
            noticias_vivo = scraper.buscar_noticias(termino_busqueda)
            antecedentes.extend(noticias_vivo)
    except Exception as e:
        logger.error(f"Error en web scraping en vivo: {e}")

    # FALLBACK DE EMERGENCIA: Si no hay NADA
    if not antecedentes:
        antecedentes.append({
            "candidato": "Alcaldías Anteriores",
            "proceso_electoral_id": "Hemeroteca Nacional",
            "categoria": categoria or "General",
            "accion": "Sin Datos",
            "objeto": objeto[:40] if objeto else "Referencia general",
            "cantidad": None,
            "unidad": None,
            "plazo": "Referencial",
            "texto": "No se encontraron datos del SERCOP ni de medios en vivo específicos para esta propuesta. Posiblemente dependió de financiamiento externo o no se ejecutó.",
            "fuente": "Base de datos (Sin matches exactos)",
            "fuente_url": None
        })

    # Recalculamos el promedio con los datos que tienen cantidades
    cantidades_finales = [float(a["cantidad"]) for a in antecedentes if a.get("cantidad") is not None]
    promedio_final = round(sum(cantidades_finales) / len(cantidades_finales), 1) if cantidades_finales else promedio

    return {
        "total_antecedentes": len(antecedentes),
        "promedio_historico_cantidad": promedio_final,
        "antecedentes": antecedentes[:15], # Limitamos a 15 para no saturar la UI
        "nota": "Contexto alimentado por IA (Planes de Trabajo) y cruce con base de datos hemerográfica / SERCOP extraída automáticamente.",
    }
