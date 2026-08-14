"""Métricas deterministas; no contienen interpretación política."""
from __future__ import annotations

from src.models.schema import Calculo, Promesa


def promedio_historico_anual(promesa: Promesa) -> Calculo | None:
    valores = [float(f.valor) for f in promesa.contexto_historico if f.valor is not None]
    if not valores:
        return None
    resultado = sum(valores) / len(valores)
    return Calculo("promedio_historico_anual", resultado, "sum(valores_historicos) / numero_de_anios")


def ritmo_requerido_anual(promesa: Promesa, anios_plazo: int | float | None) -> Calculo | None:
    if promesa.cantidad is None or anios_plazo is None or anios_plazo <= 0:
        return None
    resultado = float(promesa.cantidad) / float(anios_plazo)
    return Calculo("ritmo_requerido_anual", resultado, "cantidad_propuesta / anios_plazo")


def relacion_con_promedio_historico(ritmo: Calculo | None, promedio: Calculo | None) -> Calculo | None:
    if ritmo is None or promedio is None or promedio.resultado == 0:
        return None
    return Calculo("relacion_con_promedio_historico", ritmo.resultado / promedio.resultado, "ritmo_requerido_anual / promedio_historico_anual")


def diferencia_absoluta(ritmo: Calculo | None, promedio: Calculo | None) -> Calculo | None:
    if ritmo is None or promedio is None:
        return None
    return Calculo("diferencia_absoluta", abs(ritmo.resultado - promedio.resultado), "abs(ritmo_requerido_anual - promedio_historico_anual)")


def calcular_todos(promesa: Promesa, anios_plazo: int | float | None) -> list[Calculo]:
    promedio = promedio_historico_anual(promesa)
    ritmo = ritmo_requerido_anual(promesa, anios_plazo)
    relacion = relacion_con_promedio_historico(ritmo, promedio)
    diferencia = diferencia_absoluta(ritmo, promedio)
    return [calculo for calculo in (promedio, ritmo, relacion, diferencia) if calculo is not None]
