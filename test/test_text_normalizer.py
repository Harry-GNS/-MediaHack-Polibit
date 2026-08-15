from src.extraction.text_normalizer import evidencia_estandarizada, es_texto_presentable, estandarizar_texto


def test_estandariza_espacios_y_conserva_las_palabras_de_la_cita():
    texto = "Construcción   de  un plan\u00a0municipal\npara la gestión ambiental."
    assert estandarizar_texto(texto) == "Construcción de un plan municipal\npara la gestión ambiental."


def test_descarta_series_de_letras_fragmentadas_antes_de_mostrarlas():
    texto = "Construcción de A d C pe aoctr s n au c s aa t erl r li g u z ta ca rc ac d ii tóeón."
    assert not es_texto_presentable(texto)
    assert evidencia_estandarizada({"texto_original": texto}) is None
