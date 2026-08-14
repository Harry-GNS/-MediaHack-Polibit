"""Configuración central de Evidencia Electoral.

Carga variables de entorno y define constantes compartidas por todo el
proyecto (rutas de datos, nombres de tablas, niveles de comparación, etc.).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Rutas ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
HISTORICAL_DIR = DATA_DIR / "historical"
DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "data/evidencia.db")

# --- IA ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
STRUCTURING_MODEL = "claude-sonnet-4-6"

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
