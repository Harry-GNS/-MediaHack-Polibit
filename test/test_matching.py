import pytest
from src.matching.plazo_parser import parsear_plazo
from src.matching.calculator import calcular_ritmo, calcular_ratio
from src.matching.crosser import cruzar_propuesta

def test_parsear_plazo():
    assert parsear_plazo("100 días") == pytest.approx(100/365.0)
    assert parsear_plazo("primer año") == 1.0
    assert parsear_plazo("en toda mi administración") == 4.0
    assert parsear_plazo("hasta 2029") == 4.0
    assert parsear_plazo("3.5 años") == 3.5
    assert parsear_plazo(None) == 4.0

def test_calcular_ritmo():
    assert calcular_ritmo(1000, 4) == 250.0
    assert calcular_ritmo(None, 4) is None
    assert calcular_ritmo(1000, 0) is None

def test_calcular_ratio():
    assert calcular_ratio(100, 50) == 2.0
    assert calcular_ratio(100, 0) is None
    assert calcular_ratio(None, 50) is None

@pytest.fixture
def catalogo_mock():
    return [
        {
            "sector": "Seguridad",
            "subtema": "Policía Nacional",
            "indicador": "Nuevos Policías",
            "unidad": "efectivos",
            "promedio_anual": 3000,
            "monto_historico_usd": 100000,
            "periodo": "2018-2023",
            "fuente": "Ministerio del Interior"
        },
        {
            "sector": "Educación",
            "unidad": "escuelas",
            "promedio_anual": 10,
            "periodo": "2015-2022"
        }
    ]

def test_cruce_directa(catalogo_mock):
    propuesta = {
        "sector": "Seguridad",
        "cantidad_objetivo": 12000,
        "unidad": "efectivos",
        "plazo": "4 años"
    }
    resultado = cruzar_propuesta(propuesta, catalogo_mock)
    
    assert resultado["nivel_comparacion"] == "directa"
    assert resultado["calculos"]["ritmo_anual_requerido"] == 3000.0
    assert resultado["calculos"]["ratio_vs_historico"] == 1.0
    assert any("El ritmo requerido es 1.00 veces el promedio" in a for a in resultado["alertas"])
    assert any("Presupuesto no especificado" in a for a in resultado["alertas"])

def test_cruce_relacionada(catalogo_mock):
    propuesta = {
        "sector": "Educación",
        "descripcion": "Mejorar la educación y modernizar currículo",
        "cantidad_objetivo": None
    }
    resultado = cruzar_propuesta(propuesta, catalogo_mock)
    
    assert resultado["nivel_comparacion"] == "relacionada"
    assert resultado["calculos"] is None
    assert resultado["historico_referencia"]["sector"] == "Educación"
    assert any("Contexto histórico asociado al sector 'Educación'" in a for a in resultado["alertas"])

def test_cruce_no_disponible(catalogo_mock):
    propuesta = {
        "sector": "Criptomonedas Estatales",
        "cantidad_objetivo": 5,
        "unidad": "leyes"
    }
    resultado = cruzar_propuesta(propuesta, catalogo_mock)
    
    assert resultado["nivel_comparacion"] == "no_disponible"
    assert resultado["calculos"] is None
    assert resultado["historico_referencia"] is None
    assert any("No existe serie histórica oficial" in a for a in resultado["alertas"])
