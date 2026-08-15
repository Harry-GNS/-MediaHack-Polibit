from fastapi.testclient import TestClient

import main
import src.api.main as api
from src.api.main import app


def test_lista_procesos_para_el_menu():
    respuesta = TestClient(app).get("/procesos-electorales")
    assert respuesta.status_code == 200
    procesos = respuesta.json()
    proceso_general = next(proceso for proceso in procesos if proceso["id"] == "generales_2025")
    proceso_municipal = next(proceso for proceso in procesos if proceso["id"] == "seccionales_2023")
    assert "Parlamentarios Andinos" in proceso_general["dignidades_disponibles"]
    assert proceso_municipal["candidaturas_verificadas"] == 1


def test_entrega_interfaz_municipal():
    respuesta = TestClient(app).get("/comparacion")
    assert respuesta.status_code == 200
    assert "Evidencia Municipal" in respuesta.text
    assert "Pregunta a los planes" in respuesta.text
    assert "Selecciona un cantón" in respuesta.text
    assert "Elecciones seccionales municipales" in respuesta.text


def test_procesa_plan_descargado_con_la_ruta_del_manifiesto(monkeypatch):
    candidatura = type(
        "Candidatura",
        (),
        {
            "id": "quito-cand",
            "nombre": "Candidata Quito",
            "proceso_electoral_id": "seccionales_2023",
            "dignidad": "Alcaldía de Quito",
            "organizacion_politica": None,
            "resumen": lambda self: {"id": self.id, "nombre": self.nombre},
        },
    )()

    class _Scraper:
        def descubrir_candidaturas(self, proceso_id):
            return [candidatura]

        def descargar_planes(self, proceso_id, candidaturas):
            return {"documentos": [{"id": "quito-cand", "archivo_local": "data/raw/seccionales_2023/quito-cand.pdf"}]}

    llamadas = []
    monkeypatch.setattr(api, "ScraperCNE", _Scraper)
    monkeypatch.setattr(main, "correr_flujo", lambda *args: llamadas.append(args))

    respuesta = TestClient(app).post(
        "/procesos-electorales/seccionales_2023/procesar-planes",
        json={"candidato_ids": ["quito-cand"], "max_fragmentos": 40},
    )

    assert respuesta.status_code == 202
    estado = TestClient(app).get(f"/procesamientos/{respuesta.json()['trabajo_id']}")
    assert estado.json()["estado"] == "completado"
    assert llamadas[0][0].endswith("quito-cand.pdf")
