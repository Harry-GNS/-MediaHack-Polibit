# MediaHack Polibit

Repositorio creado durante el hackathon MediaHack II: Inteligencia Artificial, Democracia y Desinformación Electoral.

## Flujo de planes oficiales del CNE

El frontend primero consulta `GET /procesos-electorales`, presenta esas opciones
en su selector y luego usa `GET /procesos-electorales/{id}/candidaturas`. Al
confirmar candidatos, llama a `POST /procesos-electorales/{id}/descargar-planes`
con `{"candidato_ids": ["..."]}`. Sólo se siguen y descargan URLs bajo
`cne.gob.ec`; cada descarga se registra con URL fuente, fecha y SHA-256 en
`data/raw/<proceso>/manifest.json`.

```powershell
uvicorn src.api.main:app --reload
```

Abre `http://127.0.0.1:8000` para la interfaz. La vista está enfocada en
elecciones seccionales municipales: proceso, cantón, candidaturas y evidencia
por página. El panel “Pregunta a los planes” usa OpenRouter sólo desde el
backend y devuelve las promesas consultadas; no expone la clave al navegador.
Los documentos que no correspondan a una alcaldía se señalan expresamente como
demostración técnica, para no presentarlos como comparación municipal directa.

Para procesar uno de los PDFs ya descargados se necesita una clave de OpenRouter.
No guardes la clave en el repositorio ni la compartas en el chat. Elige en
OpenRouter un modelo de texto con capacidad de seguir instrucciones y define
su identificador exacto en `OPENROUTER_MODEL`.

```powershell
$env:OPENROUTER_API_KEY = "..."
$env:OPENROUTER_MODEL = "proveedor/modelo"
python main.py --pdf data/raw/seccionales/<archivo>.pdf --candidato-id <id> --candidato-nombre "<nombre>" --proceso-electoral-id seccionales_2027 --dignidad "Alcaldía de <cantón>" --organizacion-politica "<organización>"
```
