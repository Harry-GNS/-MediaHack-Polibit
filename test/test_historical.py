from src.data.historical_loader import HistoricalDataLoader


def test_cargar_dataset_educacion():
    loader = HistoricalDataLoader()
    historico = loader.cargar_csv("educacion_unidades_educativas.csv")
    
    assert len(historico) == 4
    assert historico[0].anio == 2022
    assert historico[0].valor == 12.0
    assert historico[0].nombre_fuente == "SERCOP"


def test_buscar_contexto_por_categoria():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="educacion", objeto="unidades educativas")
    
    assert len(resultado) > 0
    assert resultado[0].unidad == "unidades"


def test_buscar_contexto_no_existente_retorna_vacio():
    loader = HistoricalDataLoader()
    resultado = loader.buscar_contexto_historico(categoria="transporte", objeto="tren bala")
    
    assert resultado == []