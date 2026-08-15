# MediaHack Polibit

Repositorio creado durante el hackathon MediaHack II: Inteligencia Artificial, Democracia y Desinformación Electoral.

## Flujo de planes oficiales del CNE

El frontend primero consulta `GET /procesos-electorales`, presenta esas opciones
en su selector y luego usa `GET /procesos-electorales/{id}/candidaturas`. Al
confirmar candidatos, llama a `POST /procesos-electorales/{id}/descargar-planes`
con `{"candidato_ids": ["..."]}`. Sólo se siguen y descargan URLs bajo
`cne.gob.ec`; cada descarga se registra con URL fuente, fecha y SHA-256 en
`data/raw/<proceso>/manifest.json`.

El frontend de CondorLens se ejecuta separado del API. Requiere **Node.js 20.9 o
superior** (Next.js 16 no funciona con Node 14). En dos terminales ejecuta:

```powershell
# Terminal 1: API y pipeline Python
python -m uvicorn src.api.main:app --reload --port 8000
```

```powershell
# Terminal 2: frontend Next.js
cd frontend
npm ci
npm run dev -- --port 3000
```

Abre `http://127.0.0.1:3000/comparacion` para la interfaz. La vista está enfocada en
elecciones seccionales municipales: proceso, cantón, candidaturas y evidencia
por página. El panel “Pregunta a los planes” usa OpenRouter sólo desde el
backend y devuelve las promesas consultadas; no expone la clave al navegador.
Los documentos que no correspondan a una alcaldía se señalan expresamente como
demostración técnica, para no presentarlos como comparación municipal directa.

Para procesar se usa una clave de OpenRouter en un archivo `.env` local (nunca
en `config.py`, Git o el chat). Elige en OpenRouter un modelo de texto con
capacidad de seguir instrucciones y define su identificador exacto en
`OPENROUTER_MODEL`.

```powershell
@"
OPENROUTER_API_KEY=tu_clave_local
OPENROUTER_MODEL=proveedor/modelo
"@ | Set-Content .env

python main.py --cne-proceso-id seccionales_2023 --cne-candidatura-id seccionales-2023-alcaldia-antonio-ante-martha-posso
```

El segundo comando no requiere escribir una ruta ni cargar un PDF a mano:
descubre la candidatura registrada, descarga su plan desde el dominio oficial
del CNE, crea `data/raw/seccionales_2023/manifest.json` (URL, fecha y SHA-256)
y luego lo procesa. La fuente histórica oficial del CNE confirma que el portal
de 2023 incluía planes de alcaldías; dicho portal ya no responde de forma
estable, por lo que el catálogo inicial contiene solamente documentos que aún
se pueden verificar y descargar del CNE. No se completa el resto con datos de
terceros ni se fingen candidaturas. Al reabrirse/publicarse un índice del CNE,
se añade como fuente en `src/ingest/cne_scraper.py`.

Para un PDF que ya haya sido descargado por este flujo, la alternativa es:

```powershell
python main.py --pdf data/raw/seccionales_2023/seccionales-2023-alcaldia-antonio-ante-martha-posso.pdf --candidato-id seccionales-2023-alcaldia-antonio-ante-martha-posso --candidato-nombre "Martha Posso Padilla" --proceso-electoral-id seccionales_2023 --dignidad "Alcaldía de Antonio Ante"
```
