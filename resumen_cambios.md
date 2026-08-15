# Resumen de Cambios y Web Scraping

Este documento explica las mejoras que implementamos para lograr que el validador procese exitosamente cualquier noticia mediante web scraping e Inteligencia Artificial, resolviendo los errores iniciales.

## 1. ¿Qué hicimos?

1. **Corrección de Entorno y Dependencias:** Se solucionaron los errores iniciales de inicio de `uvicorn` (como el `ModuleNotFoundError`) instalando correctamente las dependencias requeridas (incluyendo `pdfplumber`, `beautifulsoup4`, etc.) en el entorno de Python 3.12.
2. **Ampliación de la Lógica de Validación:** El código estaba programado originalmente para buscar únicamente "datos estadísticos" usando expresiones regulares. Modificamos el enfoque para que ahora evalúe **el texto completo ingresado por el usuario**, permitiendo verificar cualquier tipo de afirmación.
3. **Mejora del Web Scraper:** El motor de extracción de texto de la web fue optimizado para atrapar todo el contenido útil de una noticia, saltándose menús de navegación y anuncios.
4. **Manejo Inteligente del Modelo de IA:** Nos aseguramos de poder utilizar modelos conversacionales como `deepseek-chat-v3.1` añadiendo un filtro (Regex) que es capaz de "pescar" la respuesta en formato JSON e ignorar la charla extra que la IA suele añadir (ej. *"Aquí tienes el análisis..."*).
5. **Ampliación de la Memoria (Contexto):** Multiplicamos la cantidad de texto de la fuente que se le envía a la Inteligencia Artificial (pasamos de 4,000 caracteres a 30,000) para garantizar que las noticias largas o el contenido escondido no se queden por fuera de la revisión.

---

## 2. Partes Claves del Código (Web Scraping y Validación)

A continuación se destacan los archivos modificados que hacen que el sistema sea funcional:

### A. Extracción de Texto (Web Scraper)
**Archivo:** [`app.py`](file:///C:/Users/Logan/OneDrive%20-%20Escuela%20Politécnica%20Nacional/Escritorio/-MediaHack-Polibit/app.py)

En este archivo habita la lógica central de la lectura web. Anteriormente, solo se leía el contenido que estaba encapsulado dentro de etiquetas `<p>` (párrafos). Sin embargo, muchas páginas modernas guardan su texto en divisiones (`<div>`) o listas (`<li>`).

El cambio clave implementado para extraer todo limpiamente es:
```python
# Ubicamos el contenedor principal de la noticia (article o main)
contenedor = soup.find("article") or soup.find("main") or soup.body
if contenedor:
    # Eliminamos basura (scripts, estilos, navegación, pie de página)
    for element in contenedor(["script", "style", "nav", "footer"]):
        element.decompose()
        
    # Extraemos texto de párrafos, listas y spans
    for p in contenedor.find_all(["p", "li", "span"]):
        texto = p.get_text(strip=True)
        # Filtramos textos basura o muy cortos y evitamos duplicados
        if len(texto) > 20 and texto not in resultado["parrafos"]:
            resultado["parrafos"].append(texto)
```

### B. Comunicación con la IA y JSON Seguro
**Archivo:** [`src/validation/validator.py`](file:///C:/Users/Logan/OneDrive%20-%20Escuela%20Politécnica%20Nacional/Escritorio/-MediaHack-Polibit/src/validation/validator.py)

1. **Aumento de la Memoria:** Para que el modelo pueda leer la noticia entera, aumentamos el límite de `[:4000]` a `[:30000]` caracteres al momento de leer la fuente scrapeada:
   ```python
   from app import texto_completo
   contenido = texto_completo(fuente)[:30000]
   ```

2. **Regex para JSON:** Modelos como DeepSeek tienden a añadir texto antes del resultado JSON. Añadimos una expresión regular (`re.search`) para evitar el error silencioso de descodificación:
   ```python
   import re
   match = re.search(r'\{.*\}', content, re.DOTALL)
   if match:
       content = match.group(0)
   ```

3. **Flexibilidad en el Prompt (`_SYSTEM_PROMPT`):** Le indicamos a la IA que no sea excesivamente rígida y que si hablan del mismo evento con variaciones, lo entienda como coincidencia en lugar de simplemente botar un "no_encontrado".
   ```python
   "Si la fuente habla de la misma noticia, temática o evento, y la información es similar o parecida, debes marcarlo como 'concordante'. "
   ```

### C. Flexibilidad de Peticiones del Usuario
**Archivo:** [`src/api/main.py`](file:///C:/Users/Logan/OneDrive%20-%20Escuela%20Politécnica%20Nacional/Escritorio/-MediaHack-Polibit/src/api/main.py)

El sistema estaba configurado para lanzar un error **HTTP 422** en cuanto el usuario enviara un texto corto (menos de 10 caracteres). 
Redujimos el límite inferior de Pydantic a 1 para permitir pruebas libres:
```python
class ValidarRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=8000, description="Texto a validar")
```
