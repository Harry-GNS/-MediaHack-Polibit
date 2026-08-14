import csv
from datetime import date
from pathlib import Path
from typing import List, Optional

from config import HISTORICAL_DIR
from src.models.schema import FuenteHistorica


class HistoricalDataLoader:
    """Carga y gestiona datasets históricos oficiales desde data/historical/."""

    def __init__(self, historical_dir: Optional[Path] = None):
        self.historical_dir = historical_dir or HISTORICAL_DIR
        self._cache = {}

    def cargar_csv(self, filename: str) -> List[FuenteHistorica]:
        """Lee un archivo CSV y devuelve una lista de objetos FuenteHistorica."""
        file_path = self.historical_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo histórico: {file_path}")

        if filename in self._cache:
            return self._cache[filename]

        fuentes = []
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fuente = FuenteHistorica(
                    nombre_fuente=row.get("nombre_fuente", "SERCOP"),
                    url_o_id=row.get("url_o_id", ""),
                    fecha_consulta=date.today(),
                    fragmento_original=row.get("fragmento_original", ""),
                    anio=int(row["anio"]) if row.get("anio") else None,
                    valor=float(row["valor"]) if row.get("valor") else None,
                    unidad=row.get("unidad", "unidades"),
                )
                fuentes.append(fuente)

        self._cache[filename] = fuentes
        return fuentes

    def buscar_contexto_historico(self, categoria: str, objeto: str) -> List[FuenteHistorica]:
        """Busca el dataset histórico correspondiente según la categoría y objeto."""
        cat_norm = categoria.strip().lower()
        obj_norm = objeto.strip().lower()

        # Mapeo de categorías/objetos a archivos CSV
        if cat_norm == "educacion" or "educativa" in obj_norm or "escuela" in obj_norm:
            return self.cargar_csv("educacion_unidades_educativas.csv")
        elif cat_norm == "seguridad" or "patrullero" in obj_norm or "camara" in obj_norm:
            return self.cargar_csv("seguridad_patrulleros.csv")
        
        return []