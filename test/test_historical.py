from src.data.historical_loader import HistoricalDataLoader


def test_cargar_dataset_educacion():
    loader = HistoricalDataLoader()
    historico = loader.cargar_csv("educacion_unidades_educativas.csv")
    assert len(historico) == 4
    assert historico[0].anio == 2022
    assert historico[0].valor == 12.0


def test_buscar_contexto_movilidad():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="movilidad", objeto="paradas y buses")
    assert len(resultado) == 4
    assert resultado[0].unidad == "unidades"


def test_buscar_contexto_ambiente_animal():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="animal", objeto="esterilizaciones")
    assert len(resultado) == 4
    assert resultado[0].valor == 15000.0


def test_buscar_contexto_salud():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="salud", objeto="puntos de atencion medica")
    assert len(resultado) == 4


def test_buscar_contexto_no_existente_retorna_vacio():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="espacio", objeto="viajes a marte")
    assert resultado == []