"""Persistencia SQLite mínima para no bloquear el flujo de extracción."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from config import DATABASE_PATH
from src.models.schema import Candidato, Promesa


def _conexion() -> sqlite3.Connection:
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


def inicializar_db() -> None:
    with _conexion() as conexion:
        conexion.execute("CREATE TABLE IF NOT EXISTS candidatos (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, datos_json TEXT NOT NULL)")
        conexion.execute("CREATE TABLE IF NOT EXISTS promesas (id TEXT PRIMARY KEY, candidato_id TEXT NOT NULL, datos_json TEXT NOT NULL)")


def guardar_candidato(candidato: Candidato) -> None:
    with _conexion() as conexion:
        conexion.execute(
            "INSERT OR REPLACE INTO candidatos(id, nombre, datos_json) VALUES (?, ?, ?)",
            (candidato.id, candidato.nombre, json.dumps(asdict(candidato), ensure_ascii=False)),
        )


def guardar_promesa(promesa: Promesa) -> None:
    with _conexion() as conexion:
        conexion.execute(
            "INSERT OR REPLACE INTO promesas(id, candidato_id, datos_json) VALUES (?, ?, ?)",
            (promesa.id, promesa.candidato, json.dumps(asdict(promesa), ensure_ascii=False, default=str)),
        )


def listar_candidatos() -> list[dict[str, object]]:
    """Devuelve sólo candidatos con evidencia procesada disponible para UI."""
    inicializar_db()
    with _conexion() as conexion:
        filas = conexion.execute(
            """SELECT c.datos_json FROM candidatos c
               WHERE EXISTS (SELECT 1 FROM promesas p WHERE p.candidato_id = c.id)
               ORDER BY c.nombre COLLATE NOCASE"""
        ).fetchall()
    return [json.loads(fila[0]) for fila in filas]


def obtener_promesas(candidato_ids: list[str] | None = None) -> list[dict[str, object]]:
    """Obtiene evidencia local y permite restringirla a la selección de UI."""
    inicializar_db()
    consulta = "SELECT datos_json FROM promesas"
    parametros: list[str] = []
    if candidato_ids:
        marcadores = ", ".join("?" for _ in candidato_ids)
        consulta += f" WHERE candidato_id IN ({marcadores})"
        parametros = candidato_ids
    consulta += " ORDER BY candidato_id, id"
    with _conexion() as conexion:
        filas = conexion.execute(consulta, parametros).fetchall()
    return [json.loads(fila[0]) for fila in filas]
