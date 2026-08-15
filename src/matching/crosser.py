from typing import Any, Dict, List, Optional
from .plazo_parser import parsear_plazo
from .calculator import calcular_ritmo, calcular_ratio

def _buscar_coincidencia(propuesta: Dict[str, Any], catalogo: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Busca en el catálogo histórico una entrada que coincida con el sector y unidad de la propuesta."""
    sector_propuesta = propuesta.get("sector")
    unidad_propuesta = propuesta.get("unidad")
    
    if not sector_propuesta:
        return None
        
    # Primer pase: buscar match exacto de sector y unidad
    for item in catalogo:
        if item.get("sector", "").lower() == sector_propuesta.lower():
            if unidad_propuesta and item.get("unidad") == unidad_propuesta:
                return item
            
    # Segundo pase: devolver cualquier coincidencia del sector (para nivel 'relacionada')
    for item in catalogo:
        if item.get("sector", "").lower() == sector_propuesta.lower():
            return item
            
    return None

def cruzar_propuesta(propuesta: Dict[str, Any], catalogo_historico: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cruza una propuesta con datos históricos para determinar su nivel de comparación
    ('directa', 'relacionada', 'no_disponible') y genera alertas y cálculos objetivos.
    """
    resultado = propuesta.copy()
    alertas = []
    
    coincidencia = _buscar_coincidencia(propuesta, catalogo_historico)
    
    # 3. Nivel 'no_disponible'
    if not coincidencia:
        resultado["nivel_comparacion"] = "no_disponible"
        alertas.append("No existe serie histórica oficial comparable para el sector/indicador mencionado.")
        resultado["calculos"] = None
        resultado["historico_referencia"] = None
        resultado["alertas"] = alertas
        return resultado
        
    cantidad = propuesta.get("cantidad_objetivo")
    unidad_prop = propuesta.get("unidad")
    unidad_hist = coincidencia.get("unidad")
    
    # 1. Nivel 'directa'
    if cantidad is not None and isinstance(cantidad, (int, float)) and unidad_prop == unidad_hist:
        resultado["nivel_comparacion"] = "directa"
        anios = parsear_plazo(propuesta.get("plazo"))
        ritmo = calcular_ritmo(cantidad, anios)
        promedio_hist = coincidencia.get("promedio_anual")
        ratio = calcular_ratio(ritmo, promedio_hist)
        
        calculos = {
            "anios_plazo": anios,
            "ritmo_anual_requerido": ritmo,
            "promedio_historico_anual": promedio_hist,
            "ratio_vs_historico": ratio
        }
        
        if ratio is not None:
            alertas.append(f"El ritmo requerido es {ratio:.2f} veces el promedio histórico documentado ({coincidencia.get('periodo')}).")
        
        if not propuesta.get("presupuesto_estimado"):
            alertas.append("Presupuesto no especificado en el plan de gobierno.")
            
        resultado["calculos"] = calculos
        
    # 2. Nivel 'relacionada'
    else:
        resultado["nivel_comparacion"] = "relacionada"
        resultado["calculos"] = None
        alertas.append(f"Contexto histórico asociado al sector '{coincidencia.get('sector')}'.")
        if cantidad is not None:
            alertas.append("No se puede realizar comparación directa por diferencias de unidad o falta de indicador preciso equivalente.")
            
    resultado["historico_referencia"] = coincidencia
    resultado["alertas"] = alertas
    
    return resultado
