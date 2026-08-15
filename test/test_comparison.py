from src.comparison.service import comparar_promesas


def test_separa_ambitos_compartidos_y_diferencias():
    promesas = [
        {"candidato": "a", "categoria": "educación", "accion": "Mejorar", "objeto": "escuelas", "texto_original": "Mejorar escuelas", "pagina_o_seccion": "2"},
        {"candidato": "b", "categoria": "educación", "accion": "Construir", "objeto": "aulas", "texto_original": "Construir aulas", "pagina_o_seccion": "3"},
        {"candidato": "a", "categoria": "movilidad", "accion": "Ampliar", "objeto": "ciclovías", "texto_original": "Ampliar ciclovías", "pagina_o_seccion": "4"},
    ]

    resultado = comparar_promesas(promesas, ["a", "b"])

    assert resultado["similitudes"][0]["ambito"] == "Educación"
    assert resultado["diferencias"][0]["ambito"] == "Movilidad"
