"""Configuración central de Evidencia Electoral.

Carga variables de entorno y define constantes compartidas por todo el
proyecto (rutas de datos, nombres de tablas, niveles de comparación, etc.).
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # permite importar contratos antes de instalar extras
    def load_dotenv() -> bool:
        return False

load_dotenv()

# --- Rutas ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
HISTORICAL_DIR = DATA_DIR / "historical"
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/evidencia.db")

# El CNE publica los planes en portales que pueden cambiar entre procesos.
# Estas rutas son el punto de entrada de la fuente oficial, no copias de
# terceros. Los adaptadores de src/ingest/cne_scraper.py validan los dominios
# antes de descargar un documento.
CNE_REQUEST_TIMEOUT = int(os.getenv("CNE_REQUEST_TIMEOUT", "20"))
CNE_REQUEST_DELAY_SECONDS = float(os.getenv("CNE_REQUEST_DELAY_SECONDS", "0.7"))

# --- IA (OpenRouter, API compatible con OpenAI) ---
# Nunca se escriben secretos en este archivo ni en el repositorio.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Modelo gratuito con salida JSON fiable. Si se define OPENROUTER_MODEL en .env,
# ese valor tiene prioridad para permitir elegir un modelo concreto conscientemente.
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# --- Fuentes oficiales (completar con endpoints reales durante el hackathon) ---
CNE_PLANES_URL = os.getenv("CNE_PLANES_URL", "")
DATOS_ABIERTOS_EC_URL = os.getenv("DATOS_ABIERTOS_EC_URL", "")
SERCOP_API_URL = os.getenv("SERCOP_API_URL", "")
INEC_API_URL = os.getenv("INEC_API_URL", "")

# --- Niveles de comparación válidos (sección 8 del documento) ---
NIVEL_DIRECTA = "directa"
NIVEL_RELACIONADA = "relacionada"
NIVEL_NO_DISPONIBLE = "no_disponible"
NIVELES_COMPARACION = (NIVEL_DIRECTA, NIVEL_RELACIONADA, NIVEL_NO_DISPONIBLE)

# Valor usado cuando un campo no aparece en el texto original (nunca se infiere)
NO_ESPECIFICADO = "no_especificado"
