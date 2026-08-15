import pytest
from src.validation.extractor import extraer_datos_estadisticos, DatoEstadistico


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
