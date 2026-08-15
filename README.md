# Evidencia Electoral — MediaHack Polibit

Herramienta para comparar planes de trabajo de candidaturas a alcaldías en
elecciones seccionales municipales de Ecuador. Obtiene planes oficiales del
CNE, conserva la evidencia por página y permite consultar o contrastar datos
contra fuentes públicas sin emitir recomendaciones electorales.

## Arranque rápido (Windows)

### Requisitos

- Python 3.11 a 3.13.
- Node.js 20.9+ y npm 10+ para el frontend. Compruébalo con `node --version`
  y `npm --version`.
- Git.

### 1. Clonar y preparar Python

```powershell
git clone https://github.com/Harry-GNS/-MediaHack-Polibit.git
cd -MediaHack-Polibit

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Copy-Item .env.example .env
```

La validación funciona sin clave mediante un respaldo textual local. Para
extraer promesas de PDFs y generar respuestas con IA, añade tu propia clave al
archivo `.env`, que nunca se sube al repositorio:

```env
OPENROUTER_API_KEY=tu_clave_aqui
OPENROUTER_MODEL=openai/gpt-oss-20b:free
```

### 2. Iniciar el backend

En la raíz del repositorio, con el entorno virtual activado:

```powershell
python -m uvicorn src.api.main:app --reload --port 8001
```

La documentación interactiva de la API queda disponible en
`http://127.0.0.1:8001/docs`.

### 3. Iniciar el frontend

Abre una segunda terminal en la raíz del repositorio:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev:3000
```

Abre `http://localhost:3000`.

Si el backend está en otro puerto o equipo, cambia únicamente esta variable en
`frontend/.env.local` y reinicia el frontend:

```env
BACKEND_URL=http://localhost:8001
```

## Comprobaciones antes de compartir cambios

Desde la raíz:

```powershell
python -m pytest -q
```

Desde `frontend`:

```powershell
npm run build
```

## Flujo de planes oficiales del CNE

El comparador consulta `GET /procesos-electorales`, permite seleccionar proceso
y cantón y después obtiene candidaturas mediante
`GET /procesos-electorales/{id}/candidaturas`. Al procesarlas, usa
`POST /procesos-electorales/{id}/descargar-planes`.

Sólo se siguen URL oficiales autorizadas del CNE. Cada plan descargado conserva
su URL fuente, fecha de descarga y SHA-256 en
`data/raw/<proceso>/manifest.json`.

Para procesar manualmente un PDF ya descargado:

```powershell
python main.py --pdf data/raw/seccionales/<archivo>.pdf --candidato-id <id> --candidato-nombre "<nombre>" --proceso-electoral-id seccionales_2027 --dignidad "Alcaldía de <cantón>" --organizacion-politica "<organización>"
```

## Seguridad y evidencia

- No subas `.env`, claves, `node_modules` ni entornos virtuales.
- La clave de OpenRouter sólo se usa desde el backend.
- Si el proveedor gratuito no está disponible, la validación muestra el
  fragmento textual más relacionado y señala que se usó el respaldo local.
- La aplicación no califica, recomienda ni ordena candidaturas.

## Publicar los cambios

Revisa primero los archivos que se enviarán:

```powershell
git status
git add README.md .env.example .gitignore config.py src frontend test
git commit -m "docs: simplifica instalación local"
git push origin Luis
```

Antes de ejecutar `git add`, confirma que `.env` no aparezca en `git status`.
