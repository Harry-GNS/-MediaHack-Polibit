"""Contraste textual reproducible contra páginas web públicas.

El módulo no utiliza modelos generativos ni emite veredictos sobre la verdad de
una afirmación. Recupera texto de cada URL, busca la coincidencia literal más
útil y devuelve la cita para que la persona pueda verificarla en la fuente.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

_TIMEOUT_SECONDS = 12
_MAX_RESPONSE_BYTES = 2_000_000
_USER_AGENT = "MediaHack-Evidencia/1.0 (+https://github.com/)"
_STOPWORDS = frozenset({
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "el", "ella", "en", "es", "esta",
    "este", "la", "las", "lo", "los", "más", "no", "o", "para", "por", "que", "se", "sin", "su",
    "sus", "un", "una", "unas", "unos", "y",
})


def validar_url_publica(url: str) -> str:
    """Acepta únicamente URLs HTTP(S) de hosts públicos.

    La comprobación evita que un formulario público use el servidor como proxy
    hacia localhost o redes privadas.
    """
    valor = url.strip()
    parsed = urlparse(valor)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Cada fuente debe ser una URL HTTP o HTTPS válida.")
    try:
        direcciones = socket.getaddrinfo(parsed.hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as error:
        raise ValueError("No se pudo resolver el dominio de una de las fuentes.") from error
    for _, _, _, _, address in direcciones:
        ip = ipaddress.ip_address(address[0])
        if not ip.is_global:
            raise ValueError("Las fuentes deben apuntar a sitios web públicos.")
    return valor


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def _terminos(texto: str) -> set[str]:
    return {
        palabra.casefold()
        for palabra in re.findall(r"[\wáéíóúüñ]{3,}", texto, flags=re.IGNORECASE)
        if palabra.casefold() not in _STOPWORDS
    }


def _extraer_bloques(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "aside"]):
        element.decompose()
    bloques: list[str] = []
    vistos: set[str] = set()
    for element in soup.select("article p, main p, p, li, h1, h2, h3"):
        texto = _normalizar(element.get_text(" ", strip=True))
        if len(texto) >= 40 and texto not in vistos:
            bloques.append(texto)
            vistos.add(texto)
    return bloques


def _obtener_html(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        timeout=_TIMEOUT_SECONDS,
        allow_redirects=False,
        stream=True,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").casefold()
    if "html" not in content_type:
        raise ValueError("La fuente no devolvió una página HTML legible.")
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > _MAX_RESPONSE_BYTES:
        raise ValueError("La fuente supera el tamaño máximo permitido.")
    contenido = bytearray()
    for chunk in response.iter_content(chunk_size=16_384):
        contenido.extend(chunk)
        if len(contenido) > _MAX_RESPONSE_BYTES:
            raise ValueError("La fuente supera el tamaño máximo permitido.")
    return contenido.decode(response.encoding or "utf-8", errors="replace")


def _mejor_cita(texto: str, bloques: Iterable[str]) -> tuple[str | None, int]:
    consulta = _normalizar(texto)
    consulta_limpia = consulta.casefold()
    terminos = _terminos(consulta)
    mejor: str | None = None
    mejor_puntaje = 0.0
    for bloque in bloques:
        bloque_limpio = bloque.casefold()
        if len(consulta_limpia) >= 12 and consulta_limpia in bloque_limpio:
            return bloque, 100
        terminos_bloque = _terminos(bloque)
        if not terminos or not terminos_bloque:
            continue
        cobertura = len(terminos & terminos_bloque) / len(terminos)
        precision = len(terminos & terminos_bloque) / len(terminos_bloque)
        puntaje = cobertura * 0.8 + precision * 0.2
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = bloque, puntaje
    return mejor, round(mejor_puntaje * 100)


def validar_fuentes(texto: str, fuentes: Iterable[str]) -> list[dict[str, Any]]:
    """Devuelve una fila por fuente con cita textual o causa verificable."""
    resultados: list[dict[str, Any]] = []
    for fuente in fuentes:
        try:
            bloques = _extraer_bloques(_obtener_html(fuente))
            cita, porcentaje = _mejor_cita(texto, bloques)
            coincide = cita is not None and porcentaje >= 55
            resultados.append({
                "estado": "concordante" if coincide else "no_encontrado",
                "porcentaje": porcentaje if coincide else 0,
                "diferencias": None,
                "fuente_url": fuente,
                "valor_en_fuente": cita if coincide else None,
                "alerta": (
                    "Se encontró una coincidencia textual en esta fuente; revisa la cita y el enlace original."
                    if coincide
                    else "No se encontró una coincidencia textual suficiente en el contenido legible de esta fuente."
                ),
            })
        except (requests.RequestException, ValueError, UnicodeError) as error:
            resultados.append({
                "estado": "no_encontrado",
                "porcentaje": 0,
                "diferencias": None,
                "fuente_url": fuente,
                "valor_en_fuente": None,
                "alerta": f"No se pudo consultar esta fuente: {error}",
            })
    return resultados
