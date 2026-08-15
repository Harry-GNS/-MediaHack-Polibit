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


def test_estructurador_envia_lote_y_conserva_una_evidencia_por_fragmento(monkeypatch):
    monkeypatch.setattr(modulo, "OPENROUTER_BATCH_SIZE", 8)

    class _CompletionsLote:
        def create(self, **kwargs):
            assert kwargs["max_tokens"] >= 400
            assert "arreglo JSON" in kwargs["messages"][0]["content"]
            respuesta = type("Respuesta", (), {})()
            mensaje = type("Mensaje", (), {"content": """[
                {"categoria":"seguridad","accion":"Mejorar","objeto":"iluminación","cantidad":"no_especificado","unidad":"no_especificado","presupuesto":"no_especificado","plazo":"no_especificado","indicador":"no_especificado"},
                {"categoria":"movilidad","accion":"Construir","objeto":"ciclovías","cantidad":2,"unidad":"km","presupuesto":"no_especificado","plazo":"4 años","indicador":"no_especificado"}
            ]"""})()
            respuesta.choices = [type("Eleccion", (), {"message": mensaje})()]
            return respuesta

    cliente = type("Cliente", (), {"chat": type("Chat", (), {"completions": _CompletionsLote()})()})()
    fragmentos = [
        FragmentoPromesa("Mejorar la iluminación.", pagina=1, indice_en_pagina=1),
        FragmentoPromesa("Construir 2 km de ciclovías en 4 años.", pagina=1, indice_en_pagina=2),
    ]

    promesas = estructurar_documento(fragmentos, "cand", "plan.pdf", cliente=cliente)

    assert len(promesas) == 2
    assert promesas[0].texto_original == fragmentos[0].texto
    assert promesas[1].cantidad == 2
    assert promesas[1].plazo == "4 años"


def test_muestra_rapida_cubre_el_documento_y_respeta_el_limite():
    fragmentos = [FragmentoPromesa(f"Propuesta {indice}", pagina=indice, indice_en_pagina=1) for indice in range(1, 11)]

    muestra = modulo._muestra_distribuida(fragmentos, 4)

    assert len(muestra) == 4
    assert muestra[0].pagina == 1
    assert muestra[-1].pagina == 10


def test_reintenta_lote_incompleto_en_sublotes(monkeypatch):
    monkeypatch.setattr(modulo, "OPENROUTER_BATCH_SIZE", 2)
    llamadas = []

    class _CompletionsConRecuperacion:
        def create(self, **kwargs):
            llamadas.append(kwargs)
            contenido = "[{\"categoria\":\"educacion\"}]" if "arreglo JSON" in kwargs["messages"][0]["content"] else _Bloque.text
            respuesta = type("Respuesta", (), {})()
            respuesta.choices = [type("Eleccion", (), {"message": type("Mensaje", (), {"content": contenido})()})()]
            return respuesta

    cliente = type("Cliente", (), {"chat": type("Chat", (), {"completions": _CompletionsConRecuperacion()})()})()
    fragmentos = [FragmentoPromesa("Construir una escuela", pagina=1, indice_en_pagina=1), FragmentoPromesa("Construir un parque", pagina=2, indice_en_pagina=1)]

    promesas = estructurar_documento(fragmentos, "cand", "plan.pdf", cliente=cliente)

    assert len(promesas) == 2
    assert len(llamadas) == 3


def test_estructurador_local_no_requiere_cliente_ni_tokens():
    fragmento = FragmentoPromesa("Construiremos ciclovías barriales.", pagina=7, indice_en_pagina=1)

    promesa = modulo.estructurar_documento_local([fragmento], "cand", "plan.pdf")[0]

    assert promesa.accion == "Construiremos"
    assert promesa.texto_original == fragmento.texto
    assert promesa.metadata_ia["modo"] == "local_sin_ia"
