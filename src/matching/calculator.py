from typing import Optional

def calcular_ritmo(meta_cantidad: Optional[float], anios_plazo: float) -> Optional[float]:
    """
    Calcula el ritmo anual requerido para cumplir una meta cuantitativa.
    """
    if meta_cantidad is None or anios_plazo is None or anios_plazo <= 0:
        return None
    return meta_cantidad / anios_plazo

def calcular_ratio(ritmo_requerido: Optional[float], promedio_historico: Optional[float]) -> Optional[float]:
    """
    Calcula el ratio o múltiplo entre el ritmo requerido de la propuesta
    y el promedio histórico de la misma métrica en la gestión pública.
    """
    if ritmo_requerido is None or promedio_historico is None or promedio_historico <= 0:
        return None
    return ritmo_requerido / promedio_historico
