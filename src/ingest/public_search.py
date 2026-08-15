import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)

@dataclass
class ResultadoScraping:
    titulo: str
    fragmento: str
    url: str

def buscar_antecedentes_publicos(categoria: str, objeto: str, max_results: int = 5) -> List[ResultadoScraping]:
    """
    Realiza una búsqueda web pública enfocada en dominios oficiales del CNE
    para encontrar PDFs de planes de trabajo relacionados con la promesa.
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("duckduckgo-search no está instalado. Usando fallback.")
        return []

    # Construimos el Dork de búsqueda
    terminos = []
    if categoria:
        terminos.append(f'"{categoria}"')
    if objeto:
        terminos.append(f'"{objeto}"')
    
    query = f"site:cne.gob.ec \"plan de trabajo\" {' '.join(terminos)}"
    logger.info(f"Buscando antecedentes en CNE con query: {query}")

    resultados = []
    try:
        with DDGS() as ddgs:
            # DuckDuckGo_search devuelve diccionarios con 'title', 'href', 'body'
            results = ddgs.text(query, max_results=max_results)
            if results:
                for r in results:
                    resultados.append(ResultadoScraping(
                        titulo=r.get("title", "Documento Oficial CNE"),
                        fragmento=r.get("body", ""),
                        url=r.get("href", "")
                    ))
    except Exception as e:
        logger.error(f"Error durante el scraping web de CNE: {e}")
        
    return resultados
