from src.models.schema import Promesa
from src.validation.validators import contiene_lenguaje_de_juicio, validar_promesa


def _promesa_base(**overrides) -> Promesa:
    datos = dict(
        id="p1",
        candidato="cand_a",
        categoria="educacion",
        accion="Construir",
        objeto="unidades educativas",
        texto_original="Construiremos 300 unidades educativas.",
        fuente_documento="plan_a.pdf",
        pagina_o_seccion="12",
    )
    datos.update(overrides)
    return Promesa(**datos)


def test_promesa_completa_es_valida_sin_advertencias():
    promesa = _promesa_base(presupuesto=1000, plazo="4 años", indicador="unidades entregadas")
    resultado = validar_promesa(promesa)
    assert resultado.valida
    assert resultado.advertencias == []


def test_falta_trazabilidad_es_error_no_advertencia():
    promesa = _promesa_base(texto_original="")
    resultado = validar_promesa(promesa)
    assert not resultado.valida
    assert any("texto_original" in e for e in resultado.errores)


def test_campos_faltantes_generan_advertencias_no_errores():
    promesa = _promesa_base()  # sin presupuesto, plazo ni indicador
    resultado = validar_promesa(promesa)
    assert resultado.valida  # sigue siendo válida: no inventamos, solo alertamos
    assert len(resultado.advertencias) == 3


def test_nivel_comparacion_invalido_es_error():
    promesa = _promesa_base()
    promesa.nivel_comparacion = "probablemente_cierto"  # valor inventado, no permitido
    resultado = validar_promesa(promesa)
    assert not resultado.valida


def test_alertas_no_deben_contener_lenguaje_de_juicio():
    assert contiene_lenguaje_de_juicio("Esta propuesta es inviable")
    assert contiene_lenguaje_de_juicio("El candidato miente sobre esto")
    assert not contiene_lenguaje_de_juicio("Presupuesto no especificado en el plan.")
