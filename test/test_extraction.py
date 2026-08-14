import src.extraction.ai_structurer as modulo
from src.extraction.ai_structurer import estructurar_documento
from src.extraction.segmenter import FragmentoPromesa


class _Bloque:
    text = ('{"categoria":"educacion","accion":"Construir","objeto":"unidades educativas",'
            '"cantidad":300,"unidad":"unidades","presupuesto":"no_especificado",'
            '"plazo":"4 años","indicador":"no_especificado"}')


class _MensajeRespuesta:
    content = _Bloque.text


class _Eleccion:
    message = _MensajeRespuesta()


class _Respuesta:
    choices = [_Eleccion()]


class _Completions:
    def create(self, **kwargs):
        assert kwargs["temperature"] == 0
        assert "No calcules" in kwargs["messages"][0]["content"]
        return _Respuesta()


class _Chat:
    completions = _Completions()


class _Cliente:
    chat = _Chat()


def test_estructurador_conserva_texto_pagina_y_no_infiere_ausencias():
    fragmento = FragmentoPromesa("Construiremos 300 unidades educativas durante 4 años.", pagina=12, indice_en_pagina=2)
    promesa = estructurar_documento([fragmento], "cand_a", "plan.pdf", cliente=_Cliente())[0]

    assert promesa.cantidad == 300
    assert promesa.pagina_o_seccion == "12"
    assert promesa.texto_original == fragmento.texto
    assert promesa.presupuesto == "no_especificado"
    assert promesa.indicador is None


def test_cliente_openrouter_usa_base_url_y_modelo_explicito(monkeypatch):
    monkeypatch.setattr(modulo, "OPENROUTER_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(modulo, "OPENROUTER_MODEL", "proveedor/modelo")
    cliente = modulo._cliente_por_defecto()
    assert str(cliente.base_url) == "https://openrouter.ai/api/v1/"
