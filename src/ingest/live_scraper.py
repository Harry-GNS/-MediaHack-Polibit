import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class HemerotecaScraper:
    """Realiza web scraping en vivo para buscar antecedentes en noticias reales."""
    
    def buscar_noticias(self, tema: str) -> list[dict]:
        # Usamos Bing News para no ser bloqueados y sacar noticias fidedignas reales
        query = urllib.parse.quote(f'Quito alcalde "{tema}"')
        url = f"https://www.bing.com/news/search?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            res = requests.get(url, headers=headers, timeout=8)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            resultados = []
            
            # Buscamos las tarjetas de noticias de Bing
            for r in soup.find_all('div', class_='news-card')[:3]:
                a_tag = r.find('a', class_='title')
                if not a_tag: continue
                
                link = a_tag.get('href', '')
                title = a_tag.text.strip()
                
                snippet_tag = r.find('div', class_='snippet')
                snippet = snippet_tag.text.strip() if snippet_tag else "Reportaje hemerográfico recuperado."
                
                # Intentar inferir el alcalde de la noticia
                alcalde = "Alcaldía Histórica"
                texto_busqueda = (title + " " + snippet).lower()
                if "yunda" in texto_busqueda: alcalde = "Jorge Yunda (Gestión)"
                elif "rodas" in texto_busqueda: alcalde = "Mauricio Rodas (Gestión)"
                elif "guarderas" in texto_busqueda: alcalde = "Santiago Guarderas (Gestión)"
                elif "barrera" in texto_busqueda: alcalde = "Augusto Barrera (Gestión)"
                elif "pabel" in texto_busqueda or "muñoz" in texto_busqueda: alcalde = "Pabel Muñoz (Actual)"
                
                resultados.append({
                    "candidato": alcalde,
                    "proceso_electoral_id": "Hemeroteca Web",
                    "categoria": "Noticia Histórica",
                    "accion": "Archivo",
                    "objeto": "Reportaje",
                    "cantidad": None,
                    "unidad": None,
                    "plazo": "Gestión Pasada",
                    "texto": f"{title} - {snippet}",
                    "fuente": "Diario Web (En Vivo)",
                    "fuente_url": link
                })
            return resultados
        except Exception as e:
            logger.error(f"Fallo en scraping en vivo: {e}")
            return []