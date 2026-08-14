"""Tests de src/calculations/metrics.py usando el ejemplo del documento
(sección 7: las 300 unidades educativas)."""
from src.calculations.metrics import (
    calcular_todos,
    diferencia_absoluta,
    promedio_historico_anual,
    relacion_con_promedio_historico,
    ritmo_requerido_anual,
)
from src.models.schema import FuenteHistorica, Promesa
from datetime import date


def _promesa_ejemplo() -> Promesa:
    """Recrea el ejemplo exacto de la sección 7 del documento."""
    historico = [
        FuenteHistorica(
            nombre_fuente="SERCOP", url_o_id="x", fecha_consulta=date.today(),
            fragmento_original="unidades educativas", anio=anio, valor=valor, unidad="unidades",
        )
        for anio, valor in [(2022, 12), (2023, 15), (2024, 9), (2025, 14)]
    ]
    return Promesa(
        id="p1",
        candidato="cand_a",
        categoria="educacion",
        accion="Construir",
        objeto="unidades educativas",
        cantidad=300,
        unidad="unidades",
        plazo="4 años",
        texto_original="Construiremos 300 unidades educativas durante nuestra administración.",
        fuente_documento="plan_a.pdf",
        pagina_o_seccion="12",
        contexto_historico=historico,
    )


def test_promedio_historico_anual():
    promesa = _promesa_ejemplo()
    calculo = promedio_historico_anual(promesa)
    assert calculo is not None
    assert calculo.resultado == 12.5  # (12+15+9+14)/4, como en el documento


def test_ritmo_requerido_anual():
    promesa = _promesa_ejemplo()
    calculo = ritmo_requerido_anual(promesa, anios_plazo=4)
    assert calculo is not None
    assert calculo.resultado == 75.0  # 300/4, como en el documento


def test_relacion_con_promedio_historico():
    promesa = _promesa_ejemplo()
    ritmo = ritmo_requerido_anual(promesa, anios_plazo=4)
    promedio = promedio_historico_anual(promesa)
    relacion = relacion_con_promedio_historico(ritmo, promedio)
    assert relacion is not None
    assert relacion.resultado == 6.0  # 75/12.5 = 6 veces, como en el documento


def test_calcular_todos_sin_plazo_no_falla():
    promesa = _promesa_ejemplo()
    calculos = calcular_todos(promesa, anios_plazo=None)
    # Sin plazo no se puede calcular ritmo, pero el promedio histórico sí.
    nombres = [c.nombre for c in calculos]
    assert "promedio_historico_anual" in nombres
    assert "ritmo_requerido_anual" not in nombres


def test_diferencia_absoluta():
    promesa = _promesa_ejemplo()
    ritmo = ritmo_requerido_anual(promesa, anios_plazo=4)
    promedio = promedio_historico_anual(promesa)
    diff = diferencia_absoluta(ritmo, promedio)
    assert diff.resultado == 62.5
