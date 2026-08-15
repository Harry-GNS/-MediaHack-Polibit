import pytest
from src.validation.extractor import extraer_datos_estadisticos, DatoEstadistico
from src.validation import validator
from src.validation.validator import _respaldo_local


def test_extrae_porcentaje_simple():
    texto = "El 40% de los hogares ecuatorianos vive en pobreza."
    datos = extraer_datos_estadisticos(texto)
    assert any(d.valor == 40.0 and d.unidad == "%" for d in datos)


def test_extrae_millones():
    texto = "El INEC reporta 3.2 millones de personas desempleadas."
    datos = extraer_datos_estadisticos(texto)
    assert any(d.valor == 3.2 for d in datos)


def test_extrae_tasa():
    texto = "La tasa de desempleo fue del 4.7% según el último reporte."
    datos = extraer_datos_estadisticos(texto)
    assert any(d.valor == 4.7 and d.unidad == "%" for d in datos)


def test_extrae_puntos():
    texto = "El índice subió 15 puntos porcentuales en el último año."
    datos = extraer_datos_estadisticos(texto)
    assert any(d.valor == 15.0 for d in datos)


def test_no_extrae_sin_numeros():
    texto = "El gobierno anunció nuevas políticas de empleo para el próximo año."
    datos = extraer_datos_estadisticos(texto)
    assert datos == []


def test_multiples_datos():
    texto = "La tasa de pobreza es del 25% y el desempleo alcanzó 3.1 millones de personas."
    datos = extraer_datos_estadisticos(texto)
    assert len(datos) >= 2


def test_contexto_incluido():
    texto = "Según el INEC, el 60% de la población tiene acceso a agua potable."
    datos = extraer_datos_estadisticos(texto)
    assert any("población" in d.contexto.lower() for d in datos)


def test_respaldo_local_cita_fragmento_relacionado():
    dato = DatoEstadistico(
        texto_original="Once terremotos de magnitud superior a 7 sacudieron al mundo en 2026.",
        valor=0.0,
        unidad="",
        contexto="Prueba",
    )
    fuente = {
        "url": "https://ejemplo.test/noticia",
        "titulo": "Once terremotos de magnitud superior a 7 sacudieron al mundo en 2026",
        "encabezados": [],
        "parrafos": [],
    }
    resultado = _respaldo_local(dato, fuente, "HTTP 429")

    assert resultado.estado == "concordante"
    assert resultado.porcentaje == 100
    assert resultado.valor_en_fuente == fuente["titulo"]


def test_validacion_sigue_sin_clave_de_ia(monkeypatch):
    dato = "Once terremotos de magnitud superior a 7 sacudieron al mundo en 2026."
    fuente = {
        "url": "https://ejemplo.test/noticia",
        "titulo": dato,
        "encabezados": [],
        "parrafos": [],
    }

    def sin_clave(_: str) -> dict:
        raise EnvironmentError("OPENROUTER_API_KEY no está configurada")

    monkeypatch.setattr(validator, "_llamar_openrouter", sin_clave)
    resultado = validator.validar_texto(dato, [fuente])[0]

    assert resultado.estado == "concordante"
    assert "Respaldo local" in resultado.alerta
