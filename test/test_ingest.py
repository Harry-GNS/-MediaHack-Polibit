from src.extraction.segmenter import segmentar_documento
from src.ingest.pdf_loader import PaginaTexto, _texto_mas_legible


def test_prioriza_extraccion_sin_letras_fragmentadas():
    texto_fragmentado = "2.3 C o n s t r u c c i ó n d e a g u a s"
    texto_legible = "2.3 Construcción de aguas"
    assert _texto_mas_legible(texto_fragmentado, texto_legible) == texto_legible


def test_segmentador_conserva_pagina_y_descarta_diagnostico():
    paginas = [PaginaTexto(numero=7, texto="2. Objetivos. Implementaremos 20 centros comunitarios durante los cuatro años de gestión.")]
    fragmentos = segmentar_documento(paginas)

    assert len(fragmentos) == 1
    assert fragmentos[0].pagina == 7
    assert "20 centros" in fragmentos[0].texto


def test_segmentador_reconoce_propuesta_en_infinitivo_numerada():
    paginas = [PaginaTexto(numero=12, texto="3.1. Impulsar la integración regional mediante acuerdos verificables.")]
    fragmentos = segmentar_documento(paginas)
    assert len(fragmentos) == 1
    assert fragmentos[0].pagina == 12


def test_segmentador_omite_continuacion_de_diagnostico_en_otra_pagina():
    paginas = [
        PaginaTexto(numero=4, texto="1. Diagnóstico de la situación actual. El Estado busca construir acuerdos."),
        PaginaTexto(numero=5, texto="La crisis impide implementar políticas públicas."),
        PaginaTexto(numero=6, texto="2. Objetivos. Implementar acuerdos regionales."),
    ]
    fragmentos = segmentar_documento(paginas)
    assert [fragmento.pagina for fragmento in fragmentos] == [6]
