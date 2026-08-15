"""
app.py — Módulo de Web Scraping reutilizable.
Puede ejecutarse directamente (python app.py) o importarse como función.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def scrapear_url(url: str, timeout: int = 10) -> dict:
    """
    Hace scraping de una URL y retorna su contenido estructurado.

    Args:
        url: La URL a scrapear.
        timeout: Segundos de espera máximos.

    Returns:
        dict con: url, titulo, encabezados, parrafos, imagenes, error (si falló).
    """
    resultado: dict = {
        "url": url,
        "titulo": None,
        "encabezados": [],
        "parrafos": [],
        "imagenes": [],
        "error": None,
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Título
        resultado["titulo"] = soup.title.string.strip() if soup.title else "Sin título"

        # Encabezados
        for heading in soup.find_all(["h1", "h2", "h3"]):
            texto = heading.get_text(strip=True)
            if texto:
                resultado["encabezados"].append({"nivel": heading.name.upper(), "texto": texto})

        # Párrafos y contenido general
        contenedor = soup.find("article") or soup.find("main") or soup.body
        if contenedor:
            for element in contenedor(["script", "style", "nav", "footer"]):
                element.decompose()
            for p in contenedor.find_all(["p", "li", "span"]):
                texto = p.get_text(strip=True)
                if len(texto) > 20 and texto not in resultado["parrafos"]:
                    resultado["parrafos"].append(texto)

        # Imágenes
        for img in soup.find_all("img"):
            src = img.get("src")
            alt = img.get("alt", "")
            if src:
                resultado["imagenes"].append({"src": src, "alt": alt})

    except requests.exceptions.RequestException as e:
        resultado["error"] = str(e)

    return resultado


def texto_completo(scraped: dict) -> str:
    """Concatena título + encabezados + párrafos en un solo string para búsquedas."""
    partes = []
    if scraped.get("titulo"):
        partes.append(scraped["titulo"])
    for h in scraped.get("encabezados", []):
        partes.append(h["texto"])
    partes.extend(scraped.get("parrafos", []))
    return " ".join(partes)


# ── Ejecución directa (demo) ──────────────────────────────────────────────────
if __name__ == "__main__":
    URL_DEMO = "https://www.cne.gob.ec/historia-de-la-funcion-electoral/"
    data = scrapear_url(URL_DEMO)

    if data["error"]:
        print(f"❌ Error: {data['error']}")
    else:
        print(f"Título: {data['titulo']}\n")
        print("--- Encabezados ---")
        for h in data["encabezados"]:
            print(f"  [{h['nivel']}]: {h['texto']}")
        print("\n--- Párrafos ---")
        for p in data["parrafos"]:
            print(f"  - {p}")
        print("\n--- Imágenes ---")
        for img in data["imagenes"]:
            print(f"  - {img['src']} | Alt: {img['alt']}")