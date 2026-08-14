from fastapi.testclient import TestClient

from src.api.main import app


def test_lista_procesos_para_el_menu():
    respuesta = TestClient(app).get("/procesos-electorales")
    assert respuesta.status_code == 200
    proceso = respuesta.json()[0]
    assert proceso["id"] == "generales_2025"
    assert "Parlamentarios Andinos" in proceso["dignidades_disponibles"]


def test_entrega_interfaz_municipal():
    respuesta = TestClient(app).get("/")
    assert respuesta.status_code == 200
    assert "Evidencia Municipal" in respuesta.text
    assert "Pregunta a los planes" in respuesta.text
