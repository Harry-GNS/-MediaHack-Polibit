from datetime import date
from typing import Any, List, Optional
from pydantic import BaseModel


class FuenteHistorica(BaseModel):
    nombre_fuente: str
    url_o_id: str
    fecha_consulta: date
    fragmento_original: str
    anio: Optional[int] = None
    valor: Optional[float] = None
    unidad: str = "unidades"