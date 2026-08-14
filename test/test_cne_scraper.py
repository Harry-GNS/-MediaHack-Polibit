from pathlib import Path

import src.ingest.cne_scraper as modulo
from src.ingest.cne_scraper import ScraperCNE


class _Respuesta:
    def __init__(self, texto="", contenido=b"", headers=None):
        self.text = texto
        self.content = contenido
        self.headers = headers or {}

    def raise_for_status(self):
        return None


class _Sesion:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.headers = {}

    def get(self, url, timeout):
        return self.respuestas[url]


def test_descubre_y_descarga_solo_pdf_de_cne(tmp_path, monkeypatch):
    indice = "https://www.cne.gob.ec/download-category/parlamentarios-andinos-planes-de-trabajo/"
    ficha = "https://www.cne.gob.ec/plan-unidad-popular/"
    pdf = "https://www.cne.gob.ec/wp-content/uploads/2024/11/unidad-popular.pdf"
    sesion = _Sesion({
        indice: _Respuesta('<a href="/plan-unidad-popular/">Plan de trabajo Unidad Popular</a>'),
        ficha: _Respuesta(f'<a class="wpdm-download-link" href="{pdf}">Descargar PDF</a>'),
        pdf: _Respuesta(contenido=b"%PDF-1.7 prueba", headers={"Content-Type": "application/pdf"}),
    })
    monkeypatch.setattr(modulo, "RAW_DIR", tmp_path / "raw")
    scraper = ScraperCNE(session=sesion, pausa=0)

    candidaturas = scraper.descubrir_candidaturas("generales_2025")
    assert len(candidaturas) == 1
    assert candidaturas[0].nombre == "Unidad Popular"

    manifiesto = scraper.descargar_planes("generales_2025", candidaturas)
    assert len(manifiesto["documentos"]) == 1
    assert (tmp_path / "raw" / "generales_2025" / "manifest.json").is_file()

    # Una segunda selección no debe borrar trazabilidad de la primera.
    manifiesto = scraper.descargar_planes("generales_2025", candidaturas)
    assert len(manifiesto["documentos"]) == 1


def test_rechaza_origen_fuera_del_cne():
    scraper = ScraperCNE(pausa=0)
    try:
        scraper._obtener("https://ejemplo.org/plan.pdf")
    except modulo.CNEError as error:
        assert "fuera de los dominios públicos permitidos" in str(error)
    else:
        raise AssertionError("Debía rechazar una URL ajena al CNE")


def test_expone_plan_municipal_verificado_sin_inventar_catalogo():
    candidaturas = modulo.PROCESOS_ELECTORALES["seccionales_2023"].candidaturas_directas

    assert len(candidaturas) == 1
    candidatura = candidaturas[0]
    assert candidatura.nombre == "Martha Posso Padilla"
    assert candidatura.territorio == "Antonio Ante"
    assert candidatura.dignidad == "Alcaldía de Antonio Ante"
    assert candidatura.plan_url.startswith("https://delegaciones.cne.gob.ec/")
