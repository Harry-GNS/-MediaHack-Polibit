from src.questions.answerer import seleccionar_evidencias


def test_selecciona_evidencia_relevante_a_la_pregunta():
    promesas = [
        {"id": "p1", "categoria": "seguridad", "accion": "Mejorar", "objeto": "iluminación", "texto_original": "Mejorar la iluminación de parques."},
        {"id": "p2", "categoria": "movilidad", "accion": "Ampliar", "objeto": "ciclovías", "texto_original": "Ampliar las ciclovías barriales."},
    ]
    evidencia = seleccionar_evidencias("¿Qué propone sobre iluminación y seguridad?", promesas)
    assert evidencia[0]["id"] == "p1"
