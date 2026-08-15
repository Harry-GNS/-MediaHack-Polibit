from fastapi.testclient import TestClient

import src.api.main as api
from src.api.main import app


def test_validar_devuelve_una_fila_por_fuente(monkeypatch):
    monkeypatch.setattr(api, "validar_fuentes", lambda texto, fuentes: [{
        "estado": "concordante",
        "porcentaje": 100,
        "diferencias": None,
        "fuente_url": fuentes[0],
        "valor_en_fuente": texto,
        "alerta": "Coincidencia textual.",
    }])
    monkeypatch.setattr(api, "validar_url_publica", lambda fuente: fuente)

    respuesta = TestClient(app).post("/validar", json={
        "texto": "El municipio ampliará el acceso al agua potable.",
        "fuentes": ["https://ejemplo.gob.ec/plan"],
    })

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["estado"] == "concordante"
    assert respuesta.json()[0]["valor_en_fuente"].startswith("El municipio")


def test_validar_rechaza_fuentes_no_publicas():
    respuesta = TestClient(app).post("/validar", json={
        "texto": "Una frase comprobable.",
        "fuentes": ["http://127.0.0.1:8000/privado"],
    })

    assert respuesta.status_code == 422
