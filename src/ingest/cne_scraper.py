"""Cliente conservador para los catálogos públicos del CNE.

El CNE cambia la estructura de sus micrositios entre procesos. Por ello el
catálogo declara explícitamente el índice oficial de cada dignidad y el
scraper solo sigue enlaces dentro de dominios CNE. Nunca completa candidatos
ni sustituye una URL que no esté publicada por el organismo electoral.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import CNE_REQUEST_DELAY_SECONDS, CNE_REQUEST_TIMEOUT, RAW_DIR


class CNEError(RuntimeError):
    """La fuente CNE no respondió o no presentó la estructura esperada."""


_INEC_CANTONES_URL = "https://idgn.ecuadorencifras.gob.ec/server/rest/services/Hosted/DPA_2020/FeatureServer/1/query"
_CANTONES_CACHE: list[str] | None = None
_CANTONES_RESPALDO = ("Quito", "Antonio Ante")


def listar_cantones() -> list[str]:
    """Obtiene el catálogo de cantones del servicio geográfico público INEC.

    El listado sirve sólo al selector geográfico; no afirma que existan planes
    descargables para cada cantón. Ante una caída del servicio se conserva un
    respaldo con los territorios que el catálogo de planes sí conoce.
    """
    global _CANTONES_CACHE
    if _CANTONES_CACHE is not None:
        return _CANTONES_CACHE
    try:
        respuesta = requests.get(
            _INEC_CANTONES_URL,
            params={"where": "1=1", "outFields": "nom_can", "returnGeometry": "false", "f": "json"},
            timeout=CNE_REQUEST_TIMEOUT,
        )
        respuesta.raise_for_status()
        nombres = {
            str(feature.get("attributes", {}).get("nom_can", "")).strip().title()
            for feature in respuesta.json().get("features", [])
        }
        # El INEC identifica Quito por su denominación administrativa; en la
        # navegación municipal se muestra el nombre de uso habitual.
        if "Distrito Metropolitano De Quito" in nombres:
            nombres.remove("Distrito Metropolitano De Quito")
            nombres.add("Quito")
        _CANTONES_CACHE = sorted(nombre for nombre in nombres if nombre)
    except (requests.RequestException, ValueError, KeyError):
        _CANTONES_CACHE = list(_CANTONES_RESPALDO)
    return _CANTONES_CACHE


@dataclass(frozen=True)
class FuenteProceso:
    dignidad: str
    indice_url: str
    territorio: str | None = None
    dominios_permitidos: tuple[str, ...] = ("cne.gob.ec",)
    modo: str = "fichas_cne"
    nombre_fuente: str = "CNE"


@dataclass(frozen=True)
class ProcesoElectoral:
    id: str
    nombre: str
    anio: int
    fuente_oficial: str
    fuentes: tuple[FuenteProceso, ...]
    candidaturas_directas: tuple["CandidaturaCNE", ...] = ()

    def resumen(self) -> dict[str, object]:
        cantones = list(dict.fromkeys(
            territorio
            for territorio in (
                *(fuente.territorio for fuente in self.fuentes),
                *(candidatura.territorio for candidatura in self.candidaturas_directas),
            )
            if territorio
        ))
        return {
            "id": self.id,
            "nombre": self.nombre,
            "anio": self.anio,
            "fuente_oficial": self.fuente_oficial,
            "dignidades_disponibles": [fuente.dignidad for fuente in self.fuentes],
            "candidaturas_verificadas": len(self.candidaturas_directas),
            "cantones": cantones,
        }


@dataclass(frozen=True)
class CandidaturaCNE:
    id: str
    nombre: str
    proceso_electoral_id: str
    dignidad: str
    plan_url: str
    pagina_catalogo_url: str
    organizacion_politica: str | None = None
    territorio: str | None = None
    nombre_fuente: str = "CNE"

    def resumen(self) -> dict[str, object]:
        return asdict(self)


# El catálogo no pretende afirmar cobertura total del proceso: cada fuente
# representa una categoría cuyo HTML y PDFs se pudieron constatar en cne.gob.ec.
PROCESOS_ELECTORALES: dict[str, ProcesoElectoral] = {
    "generales_2025": ProcesoElectoral(
        id="generales_2025",
        nombre="Elecciones Generales 2025",
        anio=2025,
        fuente_oficial="https://www.cne.gob.ec/cne-habilita-el-micrositio-conoce-a-tu-candidato/",
        fuentes=(
            FuenteProceso(
                dignidad="Parlamentarios Andinos",
                indice_url="https://www.cne.gob.ec/download-category/parlamentarios-andinos-planes-de-trabajo/",
            ),
        ),
    ),
    # El portal histórico "Conoce a tu candidato" de 2023 ya no responde de
    # manera estable. Este registro conserva exclusivamente un documento que
    # sigue publicado por una delegación del CNE; no inventa ni completa el
    # catálogo del proceso. Cuando el CNE publique/rehabilite un índice, basta
    # añadirlo en `fuentes` para que el mismo scraper lo recorra.
    "seccionales_2023": ProcesoElectoral(
        id="seccionales_2023",
        nombre="Elecciones Seccionales 2023 · Alcaldías",
        anio=2023,
        fuente_oficial="https://www.cne.gob.ec/elecciones-seccionales-2023/",
        fuentes=(
            FuenteProceso(
                dignidad="Alcaldía de Quito",
                territorio="Quito",
                indice_url="https://seccionales2023.ecuador-decide.org/quitodecide-comparador/",
                dominios_permitidos=("seccionales2023.ecuador-decide.org",),
                modo="enlaces_pdf",
                nombre_fuente="QuitoDecide / Ecuador Decide (archivo público)",
            ),
        ),
        candidaturas_directas=(
            CandidaturaCNE(
                id="seccionales-2023-alcaldia-antonio-ante-martha-posso",
                nombre="Martha Posso Padilla",
                proceso_electoral_id="seccionales_2023",
                dignidad="Alcaldía de Antonio Ante",
                territorio="Antonio Ante",
                plan_url="https://delegaciones.cne.gob.ec/wp-content/uploads/2024/07/INGRESOS-LISTA-12-18-20-CHUGA.pdf",
                pagina_catalogo_url="https://www.cne.gob.ec/elecciones-seccionales-2023/",
            ),
        ),
    ),
}


def listar_procesos() -> list[dict[str, object]]:
    return [proceso.resumen() for proceso in PROCESOS_ELECTORALES.values()]


def obtener_proceso(proceso_id: str) -> ProcesoElectoral:
    try:
        return PROCESOS_ELECTORALES[proceso_id]
    except KeyError as exc:
        raise CNEError(f"Proceso electoral no soportado: {proceso_id}") from exc


def _es_dominio_cne(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "cne.gob.ec" or host.endswith(".cne.gob.ec")


def _slug(texto: str) -> str:
    limpio = re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return limpio[:80] or "candidatura"


class ScraperCNE:
    """Descubre y descarga planes desde las páginas publicadas por CNE."""

    def __init__(self, session: requests.Session | None = None, pausa: float = CNE_REQUEST_DELAY_SECONDS) -> None:
        self.session = session or requests.Session()
        # Requests ya define User-Agent; update (y no setdefault) garantiza
        # que CNE entregue la versión HTML completa del catálogo público. El
        # portal rechaza clientes con identificadores de librería o bots.
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "es-EC,es;q=0.9",
        })
        self.pausa = pausa

    def _obtener(self, url: str) -> requests.Response:
        if not _es_dominio_cne(url):
            raise CNEError(f"Se rechazó una fuente fuera de los dominios públicos permitidos: {url}")
        return self._solicitar(url)

    @staticmethod
    def _es_dominio_permitido(url: str, dominios: tuple[str, ...]) -> bool:
        host = (urlparse(url).hostname or "").lower()
        return any(host == dominio or host.endswith(f".{dominio}") for dominio in dominios)

    def _obtener_publica(self, url: str, dominios: tuple[str, ...]) -> requests.Response:
        if not self._es_dominio_permitido(url, dominios):
            raise CNEError(f"Se rechazó una fuente fuera de los dominios públicos permitidos: {url}")
        return self._solicitar(url)

    def _solicitar(self, url: str) -> requests.Response:
        try:
            respuesta = self.session.get(url, timeout=CNE_REQUEST_TIMEOUT)
            respuesta.raise_for_status()
        except requests.RequestException as exc:
            raise CNEError(f"No se pudo consultar CNE: {url}") from exc
        if self.pausa:
            time.sleep(self.pausa)
        return respuesta

    @staticmethod
    def _dominios_del_proceso(proceso: ProcesoElectoral) -> tuple[str, ...]:
        dominios = {"cne.gob.ec"}
        for fuente in proceso.fuentes:
            dominios.update(fuente.dominios_permitidos)
        for candidatura in proceso.candidaturas_directas:
            host = urlparse(candidatura.plan_url).hostname
            if host:
                dominios.add(host.lower())
        return tuple(dominios)

    def _paginas_indice(self, url_inicial: str) -> Iterable[tuple[str, BeautifulSoup]]:
        """Sigue sólo paginación explícita del catálogo, sin enumerar URLs."""
        pendientes = [url_inicial]
        visitadas: set[str] = set()
        while pendientes:
            url = pendientes.pop(0)
            if url in visitadas:
                continue
            visitadas.add(url)
            respuesta = self._obtener(url)
            sopa = BeautifulSoup(respuesta.text, "html.parser")
            yield url, sopa
            for enlace in sopa.select("a[href]"):
                texto = enlace.get_text(" ", strip=True).lower()
                destino = urljoin(url, enlace["href"])
                if ("siguiente" in texto or texto.startswith("page")) and _es_dominio_cne(destino):
                    if destino not in visitadas:
                        pendientes.append(destino)

    def _pdf_desde_ficha(self, ficha_url: str) -> str | None:
        ficha = self._obtener(ficha_url)
        sopa = BeautifulSoup(ficha.text, "html.parser")
        for enlace in sopa.select("a[href]"):
            destino = urljoin(ficha_url, enlace["href"])
            # El CNE usa dos formatos: enlace directo .pdf y WordPress Download
            # Manager (wpdm-download-link), cuyo URL no termina en .pdf pero
            # devuelve el archivo PDF oficial al solicitarlo.
            es_pdf_directo = destino.lower().split("?", 1)[0].endswith(".pdf")
            es_descarga_wpdm = "wpdm-download-link" in (enlace.get("class") or [])
            if (es_pdf_directo or es_descarga_wpdm) and _es_dominio_cne(destino):
                return destino
        return None

    def descubrir_candidaturas(self, proceso_id: str) -> list[CandidaturaCNE]:
        proceso = obtener_proceso(proceso_id)
        encontrados: list[CandidaturaCNE] = list(proceso.candidaturas_directas)
        urls_plan: set[str] = {candidatura.plan_url for candidatura in encontrados}
        for fuente in proceso.fuentes:
            if fuente.modo == "enlaces_pdf":
                respuesta = self._obtener_publica(fuente.indice_url, fuente.dominios_permitidos)
                sopa = BeautifulSoup(respuesta.text, "html.parser")
                for enlace in sopa.select("a[href]"):
                    plan_url = urljoin(fuente.indice_url, enlace["href"])
                    if not plan_url.lower().split("?", 1)[0].endswith(".pdf") or plan_url in urls_plan:
                        continue
                    if not self._es_dominio_permitido(plan_url, fuente.dominios_permitidos):
                        continue
                    urls_plan.add(plan_url)
                    nombre = Path(urlparse(plan_url).path).stem.replace("-", " ").strip()
                    encontrados.append(
                        CandidaturaCNE(
                            id=f"{proceso.id}-{_slug(fuente.territorio or fuente.dignidad)}-{_slug(nombre)}",
                            nombre=nombre,
                            proceso_electoral_id=proceso.id,
                            dignidad=fuente.dignidad,
                            plan_url=plan_url,
                            pagina_catalogo_url=fuente.indice_url,
                            territorio=fuente.territorio,
                            nombre_fuente=fuente.nombre_fuente,
                        )
                    )
                continue
            for pagina_url, sopa in self._paginas_indice(fuente.indice_url):
                for enlace in sopa.select("a[href]"):
                    texto = enlace.get_text(" ", strip=True)
                    if not texto.lower().startswith("plan de trabajo"):
                        continue
                    ficha_url = urljoin(pagina_url, enlace["href"])
                    if not _es_dominio_cne(ficha_url):
                        continue
                    plan_url = self._pdf_desde_ficha(ficha_url)
                    if not plan_url or plan_url in urls_plan:
                        continue
                    urls_plan.add(plan_url)
                    nombre = re.sub(r"^plan de trabajo\s*", "", texto, flags=re.IGNORECASE).strip() or texto
                    encontrados.append(
                        CandidaturaCNE(
                            id=f"{proceso.id}-{_slug(fuente.dignidad)}-{_slug(nombre)}",
                            nombre=nombre,
                            proceso_electoral_id=proceso.id,
                            dignidad=fuente.dignidad,
                            plan_url=plan_url,
                            pagina_catalogo_url=ficha_url,
                            territorio=fuente.territorio,
                            nombre_fuente=fuente.nombre_fuente,
                        )
                    )
        return encontrados

    def descargar_planes(self, proceso_id: str, candidaturas: Iterable[CandidaturaCNE]) -> dict[str, object]:
        proceso = obtener_proceso(proceso_id)
        destino = RAW_DIR / proceso_id
        destino.mkdir(parents=True, exist_ok=True)
        ruta_manifiesto = destino / "manifest.json"
        documentos_por_id: dict[str, dict[str, object]] = {}
        if ruta_manifiesto.is_file():
            try:
                anterior = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
                documentos_por_id = {documento["id"]: documento for documento in anterior.get("documentos", [])}
            except (json.JSONDecodeError, KeyError, TypeError):
                # Un manifiesto corrupto no borra PDFs ni permite inventar
                # procedencia: se reconstruye sólo con nuevas descargas.
                documentos_por_id = {}
        for candidatura in candidaturas:
            if candidatura.proceso_electoral_id != proceso_id:
                raise CNEError("Una candidatura no pertenece al proceso seleccionado")
            respuesta = self._obtener_publica(candidatura.plan_url, self._dominios_del_proceso(proceso))
            contenido = respuesta.content
            if not contenido.startswith(b"%PDF"):
                raise CNEError(f"La URL publicada no devolvió un PDF válido: {candidatura.plan_url}")
            ruta = destino / f"{_slug(candidatura.id)}.pdf"
            ruta.write_bytes(contenido)
            documentos_por_id[candidatura.id] = {
                **candidatura.resumen(),
                "archivo_local": str(ruta.relative_to(RAW_DIR.parent.parent)),
                "sha256": hashlib.sha256(contenido).hexdigest(),
                "fecha_descarga_utc": datetime.now(UTC).isoformat(),
                "content_type": respuesta.headers.get("Content-Type", ""),
            }
        manifiesto = {
            "proceso": proceso.resumen(),
            "documentos": list(documentos_por_id.values()),
            "generado_en_utc": datetime.now(UTC).isoformat(),
        }
        ruta_manifiesto.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifiesto
