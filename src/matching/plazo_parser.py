import re
from typing import Optional

def parsear_plazo(texto_plazo: Optional[str], default_anios: float = 4.0) -> float:
    """
    Convierte un texto de plazo en una cantidad numérica de años.
    
    Args:
        texto_plazo: El texto a parsear (ej. '4 años', '100 días')
        default_anios: Valor por defecto si no se puede determinar el plazo.
        
    Returns:
        float: Cantidad de años estimados.
    """
    if not texto_plazo:
        return default_anios
        
    texto = texto_plazo.lower().strip()
    
    # Casos explícitos
    if "100 días" in texto or "cien días" in texto:
        return 100 / 365.0
    if "primer año" in texto or "1 año" in texto or "un año" in texto:
        return 1.0
    if "administración" in texto or "mandato" in texto or "periodo" in texto or "período" in texto:
        return 4.0
        
    # Extraer años "hasta 2029" (Asumiendo inicio de gobierno en 2025 para el contexto actual)
    match_hasta = re.search(r'hasta\s+(20\d{2})', texto)
    if match_hasta:
        anio_fin = int(match_hasta.group(1))
        plazo = anio_fin - 2025
        return float(plazo) if plazo > 0 else default_anios

    # Extraer número genérico de años, ej: "4 años", "en 2.5 años"
    match_anios = re.search(r'(\d+(?:\.\d+)?)\s*año', texto)
    if match_anios:
        return float(match_anios.group(1))
        
    return default_anios
