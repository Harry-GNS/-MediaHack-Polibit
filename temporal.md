
\documentclass[11pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot]{babel}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{parskip}

\geometry{margin=2.3cm}
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    urlcolor=blue,
    pdftitle={Propuesta - Evidencia Electoral},
    pdfauthor={Equipo de desarrollo}
}

\titleformat{\section}{\Large\bfseries}{\thesection.}{0.5em}{}
\titleformat{\subsection}{\large\bfseries}{\thesubsection.}{0.5em}{}

\title{\textbf{Evidencia Electoral}\\
\large Plataforma de comparación y contextualización de planes de gobierno}
\author{Propuesta de proyecto}
\date{Agosto 2026}

\begin{document}

\maketitle

\begin{abstract}
Evidencia Electoral es una plataforma orientada a ciudadanos y periodistas que transforma los planes de gobierno oficiales de candidatos ecuatorianos en información estructurada, trazable y comparable. El sistema utiliza inteligencia artificial para identificar y estructurar propuestas electorales, y las relaciona con datos históricos provenientes exclusivamente de fuentes públicas y oficiales.

La plataforma no determina si una promesa es viable, verdadera, falsa, buena o mala, ni recomienda candidatos. Su función es presentar evidencia, realizar cálculos objetivos y conservar la procedencia de cada dato para que la decisión final permanezca en manos del usuario.
\end{abstract}

\section{Problema}

Los planes de gobierno electorales contienen una gran cantidad de información distribuida en documentos extensos. Comparar varios candidatos requiere leer, localizar y organizar manualmente decenas o cientos de páginas, además de buscar por separado información histórica que permita contextualizar sus propuestas.

Esto genera tres problemas principales:

\begin{enumerate}[leftmargin=*]
    \item \textbf{Costo de análisis:} un ciudadano o periodista debe revisar numerosos documentos para encontrar propuestas comparables.
    \item \textbf{Información desestructurada:} las promesas aparecen redactadas en lenguaje natural y no siguen necesariamente una estructura común.
    \item \textbf{Falta de contexto:} conocer una promesa no permite, por sí solo, conocer cómo se relaciona con la ejecución histórica, el presupuesto o la capacidad registrada de una institución.
\end{enumerate}

El problema no es únicamente encontrar las promesas, sino convertirlas en información que pueda ser comparada con evidencia pública sin sustituir el criterio humano.

\section{Propuesta}

Evidencia Electoral será una plataforma que:

\begin{enumerate}[leftmargin=*]
    \item recibe planes de gobierno oficiales;
    \item utiliza IA para extraer propuestas y convertirlas en datos estructurados;
    \item identifica elementos como acción, objetivo, cantidad, plazo, presupuesto e indicadores;
    \item conserva la fuente exacta de cada dato extraído;
    \item busca datos históricos oficiales relacionados con cada propuesta;
    \item calcula diferencias, promedios, proporciones y otros indicadores objetivos cuando los datos lo permitan;
    \item presenta la promesa junto con su contexto histórico;
    \item permite comparar candidatos;
    \item deja la interpretación y decisión final al ciudadano o periodista.
\end{enumerate}

\section{Principio fundamental}

\begin{quote}
\textbf{``Los datos que hay detrás de cada promesa de campaña, sin veredictos: solo evidencia.''}
\end{quote}

El sistema no debe convertirse en un juez político. La inteligencia artificial se utilizará como herramienta de extracción, organización y análisis cuantitativo, no como autoridad para emitir conclusiones políticas.

\section{Qué hace y qué no hace el sistema}

\subsection{El sistema SÍ hace}

\begin{itemize}[leftmargin=*]
    \item Extrae propuestas de documentos oficiales.
    \item Estructura información escrita en lenguaje natural.
    \item Identifica cantidades, plazos, presupuestos e indicadores cuando están presentes.
    \item Señala campos que no están especificados.
    \item Relaciona propuestas con datos oficiales históricos.
    \item Realiza cálculos matemáticos reproducibles.
    \item Compara candidatos utilizando los mismos criterios de información.
    \item Muestra las fuentes originales y la ubicación del dato.
    \item Permite al usuario revisar la evidencia antes de sacar una conclusión.
\end{itemize}

\subsection{El sistema NO hace}

\begin{itemize}[leftmargin=*]
    \item No determina si una promesa es viable o inviable.
    \item No declara que un candidato miente.
    \item No clasifica candidatos como buenos o malos.
    \item No recomienda por quién votar.
    \item No asigna una ``probabilidad de éxito'' política.
    \item No interpreta una ausencia de información como una falsedad.
    \item No sustituye la investigación periodística ni el criterio ciudadano.
\end{itemize}

\section{Alcance}

\subsection{Ámbito geográfico y electoral}

El prototipo estará enfocado en \textbf{Ecuador} y, como alcance inicial, en \textbf{elecciones seccionales}. El diseño podrá ampliarse posteriormente a otros procesos electorales.

\subsection{Fuentes de entrada}

La identificación de propuestas se limitará inicialmente a \textbf{planes de gobierno oficiales y documentación electoral oficial}. No se utilizarán publicaciones de redes sociales, entrevistas o noticias como fuente primaria para determinar qué prometió un candidato.

\subsection{Datos de contexto}

Los datos utilizados para contextualizar las propuestas deberán proceder, en la medida de lo posible, de fuentes oficiales y públicas. Entre las fuentes consideradas están:

\begin{itemize}[leftmargin=*]
    \item Consejo Nacional Electoral (CNE).
    \item Datos Abiertos Ecuador.
    \item Servicio Nacional de Contratación Pública (SERCOP).
    \item Instituto Nacional de Estadística y Censos (INEC).
    \item Registro Oficial.
    \item Otras instituciones públicas que dispongan de datos relevantes y verificables.
\end{itemize}

\section{Funcionamiento general}

El flujo principal será:

\begin{center}
\textbf{Plan oficial}
$\rightarrow$
\textbf{Extracción con IA}
$\rightarrow$
\textbf{Propuestas estructuradas}
$\rightarrow$
\textbf{Fuentes históricas}
$\rightarrow$
\textbf{Cruce de datos}
$\rightarrow$
\textbf{Cálculos objetivos}
$\rightarrow$
\textbf{Comparación}
$\rightarrow$
\textbf{Decisión humana}
\end{center}

\section{Ejemplo de funcionamiento}

Supóngase que un plan de gobierno contiene la siguiente propuesta:

\begin{quote}
``Construiremos 300 unidades educativas durante nuestra administración.''
\end{quote}

La IA no debe responder si la propuesta es realista. Debe transformarla en una estructura como:

\begin{table}[h]
\centering
\begin{tabular}{>{\bfseries}p{4cm}p{9cm}}
\toprule
Campo & Valor \\
\midrule
Acción & Construir \\
Objeto & Unidades educativas \\
Cantidad & 300 \\
Plazo & Administración propuesta \\
Presupuesto & No especificado \\
Indicador & Número de unidades educativas \\
Fuente & Plan de Gobierno, página correspondiente \\
\bottomrule
\end{tabular}
\end{table}

Posteriormente, el sistema puede encontrar datos históricos oficiales relacionados:

\begin{table}[h]
\centering
\begin{tabular}{ccc}
\toprule
Año & Proyectos/unidades registrados & Gasto relacionado \\
\midrule
2022 & 12 & \$X \\
2023 & 15 & \$X \\
2024 & 9 & \$X \\
2025 & 14 & \$X \\
\bottomrule
\end{tabular}
\end{table}

Si los datos son comparables, el sistema puede calcular, por ejemplo:

\begin{itemize}[leftmargin=*]
    \item promedio histórico anual;
    \item cantidad propuesta por año;
    \item diferencia absoluta;
    \item relación entre el ritmo propuesto y el histórico;
    \item relación entre presupuesto propuesto y gasto histórico, cuando ambos estén disponibles.
\end{itemize}

El resultado podría indicar:

\begin{quote}
\textbf{Ritmo requerido:} 75 unidades/año.

\textbf{Promedio histórico registrado:} 12,5 unidades/año.

\textbf{Relación:} 6 veces el promedio histórico.
\end{quote}

El sistema se detiene ahí. El usuario decide qué significado tiene esa diferencia.

\section{Tratamiento de datos no equivalentes}

Uno de los principios metodológicos del proyecto será evitar comparaciones artificiales.

Si una promesa no tiene un indicador histórico exactamente equivalente, el sistema deberá indicarlo.

Por ejemplo:

\begin{quote}
\textbf{Comparación directa:} no disponible.

\textbf{Contexto relacionado:} se encontraron 47 contratos de infraestructura educativa entre 2022 y 2025 por un monto acumulado de \$X.
\end{quote}

Los datos relacionados no deben presentarse como si fueran equivalentes a la promesa. El sistema debe distinguir claramente entre:

\begin{enumerate}[leftmargin=*]
    \item comparación directa;
    \item contexto relacionado;
    \item ausencia de información comparable.
\end{enumerate}

\section{Modelo de una promesa}

Cada propuesta podrá representarse mediante una estructura similar a:

\begin{longtable}{>{\bfseries}p{4cm}p{10cm}}
\toprule
Campo & Descripción \\
\midrule
ID & Identificador único de la propuesta. \\
Candidato & Candidato al que pertenece. \\
Categoría & Área temática de la propuesta. \\
Acción & Verbo o acción principal. \\
Objeto & Elemento sobre el que se realiza la acción. \\
Cantidad & Valor cuantitativo, si existe. \\
Unidad & Escuelas, kilómetros, personas, dólares, etc. \\
Presupuesto & Monto indicado en el documento, si existe. \\
Plazo & Periodo o fecha indicada. \\
Indicador & Forma explícita de medir la propuesta. \\
Texto original & Fragmento correspondiente del documento. \\
Fuente & Documento oficial utilizado. \\
Página/sección & Ubicación exacta del dato. \\
Contexto histórico & Datos oficiales relacionados. \\
Cálculos & Operaciones realizadas sobre los datos. \\
Nivel de comparación & Directa, relacionada o no disponible. \\
\bottomrule
\end{longtable}

\section{Trazabilidad y procedencia}

La trazabilidad será una característica central del sistema.

Cada dato mostrado deberá poder responder a la pregunta:

\begin{quote}
\textbf{``¿De dónde salió este dato?''}
\end{quote}

Por ello, siempre que sea técnicamente posible, se conservarán:

\begin{itemize}[leftmargin=*]
    \item nombre de la fuente;
    \item URL o identificador del recurso;
    \item documento original;
    \item página, sección o registro;
    \item fecha de consulta;
    \item fragmento original utilizado;
    \item transformación realizada por el sistema;
    \item cálculo aplicado, si corresponde.
\end{itemize}

La información generada por IA deberá poder distinguirse de la información proveniente directamente de una fuente oficial.

\section{Interfaz propuesta}

La aplicación tendrá como núcleo una vista de comparación.

\subsection{Vista general}

El usuario podrá seleccionar varios candidatos y observar sus propuestas organizadas por categorías.

Ejemplo:

\begin{table}[h]
\centering
\begin{tabular}{p{3.3cm}p{2.5cm}p{2.5cm}p{2.5cm}}
\toprule
\textbf{Propuesta} & \textbf{Candidato A} & \textbf{Candidato B} & \textbf{Candidato C} \\
\midrule
Escuelas & 300 & 150 & No especificado \\
Presupuesto & \$20M & No especificado & \$12M \\
Plazo & 4 años & 4 años & 3 años \\
Indicador & Sí & Sí & No \\
\bottomrule
\end{tabular}
\end{table}

\subsection{Vista detallada}

Al seleccionar una propuesta, el usuario podrá consultar:

\begin{itemize}[leftmargin=*]
    \item texto original;
    \item datos extraídos;
    \item fuente;
    \item contexto histórico;
    \item cálculos;
    \item documentos utilizados;
    \item diferencias entre candidatos.
\end{itemize}

\section{Alertas informativas}

Las alertas no serán juicios. Servirán para llamar la atención sobre características objetivas de los datos.

Ejemplos:

\begin{itemize}[leftmargin=*]
    \item ``Presupuesto no especificado en el plan.''
    \item ``Plazo no especificado.''
    \item ``No se encontró indicador cuantificable.''
    \item ``No existe un dato histórico directamente comparable.''
    \item ``El ritmo requerido es 4,2 veces el promedio histórico registrado.''
    \item ``La cifra de la propuesta no coincide con la unidad utilizada por la fuente histórica.''
\end{itemize}

Las alertas no deberán utilizar expresiones como ``inviable'', ``falso'', ``engañoso'' o equivalentes.

\section{Fuentes y recursos iniciales}

El prototipo podrá apoyarse en el siguiente conjunto de recursos:

\begin{longtable}{p{4cm}p{6cm}p{4cm}}
\toprule
\textbf{Fuente/recurso} & \textbf{Uso previsto} & \textbf{Tipo} \\
\midrule
CNE & Planes de gobierno y documentación electoral & Oficial \\
Datos Abiertos Ecuador & Localización de datasets públicos & Oficial/catálogo \\
SERCOP & Contrataciones, montos y proveedores & Oficial \\
INEC & Datos estadísticos y demográficos & Oficial \\
Registro Oficial & Normativa y documentación oficial & Oficial \\
spaCy & Procesamiento de lenguaje natural & Herramienta \\
Hugging Face & Modelos/datasets de IA & Herramienta/repositorio \\
Sentence Transformers & Búsqueda semántica, si fuese necesaria & Herramienta \\
\bottomrule
\end{longtable}

\section{Arquitectura inicial}

Para un prototipo de tiempo limitado se propone una arquitectura sencilla:

\begin{enumerate}[leftmargin=*]
    \item \textbf{Ingesta:} carga de PDFs oficiales.
    \item \textbf{Extracción de texto:} conversión de PDF a texto conservando páginas.
    \item \textbf{Procesamiento:} segmentación y detección de posibles propuestas.
    \item \textbf{IA estructuradora:} conversión de las propuestas a un esquema JSON definido.
    \item \textbf{Validación:} comprobaciones básicas de campos y tipos.
    \item \textbf{Base de datos:} almacenamiento de candidatos, propuestas, fuentes y datos históricos.
    \item \textbf{Cruce:} asociación entre propuestas y datasets oficiales.
    \item \textbf{Cálculos:} operaciones deterministas realizadas por código.
    \item \textbf{Frontend:} comparación y visualización de evidencia.
\end{enumerate}

\section{MVP para el prototipo}

Para evitar que el proyecto se vuelva demasiado grande, el MVP deberá concentrarse en un flujo demostrable.

\subsection*{Mínimo indispensable}

\begin{itemize}[leftmargin=*]
    \item Selección de candidatos.
    \item Carga o disponibilidad local de sus planes oficiales.
    \item Extracción automática de propuestas.
    \item Estructuración de cada propuesta.
    \item Página/fuente asociada a cada propuesta.
    \item Comparación entre candidatos.
    \item Al menos un conjunto de datos históricos oficiales.
    \item Al menos un cálculo objetivo entre propuesta e histórico.
    \item Vista detallada de la evidencia.
\end{itemize}

\subsection*{Fuera del MVP}

\begin{itemize}[leftmargin=*]
    \item Monitoreo de redes sociales.
    \item Scraping de noticias.
    \item Verificación automática de declaraciones.
    \item Predicción de cumplimiento.
    \item Clasificación de candidatos.
    \item Recomendaciones electorales.
    \item Análisis automático de viabilidad política.
\end{itemize}

\section{Criterios de confiabilidad}

El sistema deberá seguir estas reglas:

\begin{enumerate}[leftmargin=*]
    \item \textbf{No inventar datos.} Si un campo no aparece, se registra como no especificado.
    \item \textbf{No ocultar incertidumbre.} Si la comparación no es exacta, debe indicarse.
    \item \textbf{Conservar la fuente.} Todo dato debe tener procedencia.
    \item \textbf{Separar extracción de interpretación.} La IA estructura; el usuario interpreta.
    \item \textbf{Separar datos de cálculos.} Los cálculos deben ser reproducibles mediante fórmulas deterministas.
    \item \textbf{Mantener el texto original.} El usuario debe poder contrastar la extracción con el documento.
    \item \textbf{Aplicar los mismos criterios a todos los candidatos.}
\end{enumerate}

\section{Diferencial del proyecto}

El diferencial no consiste únicamente en ``usar IA para resumir planes de gobierno''. El valor está en conectar tres elementos:

\begin{center}
\textbf{Promesa}
$\quad+\quad$
\textbf{Fuente oficial}
$\quad+\quad$
\textbf{Contexto histórico}
\end{center}

Esto convierte un documento político difícil de analizar en una estructura donde el usuario puede responder preguntas como:

\begin{itemize}[leftmargin=*]
    \item ¿Qué prometió exactamente cada candidato?
    \item ¿Cuánto promete hacer?
    \item ¿En qué plazo?
    \item ¿Menciona un presupuesto?
    \item ¿Existe un indicador medible?
    \item ¿Qué ocurrió históricamente con iniciativas similares?
    \item ¿Cuánto dinero se ha ejecutado o contratado históricamente?
    \item ¿Cómo se compara esta propuesta con la de otros candidatos?
    \item ¿De dónde salió cada número?
\end{itemize}

La plataforma no responde ``quién tiene razón''. Permite que el usuario tenga mejores elementos para responderlo.

\section{Resultado esperado}

Al finalizar el prototipo, un ciudadano o periodista deberá poder seleccionar candidatos, revisar sus principales propuestas y abrir cada una para consultar sus datos estructurados, su fuente original, el contexto histórico disponible y los cálculos realizados.

El producto final será, por tanto, una herramienta de \textbf{acceso y organización de evidencia electoral}, no un sistema de recomendación política.

\section{Definición formal del proyecto}

\begin{quote}
\textbf{Evidencia Electoral} es una plataforma de inteligencia y análisis electoral que utiliza inteligencia artificial para extraer y estructurar propuestas de planes de gobierno oficiales de Ecuador, las relaciona con datos históricos provenientes de fuentes públicas y oficiales, y realiza comparaciones y cálculos objetivos manteniendo la trazabilidad de cada dato. La plataforma no emite juicios sobre la viabilidad, veracidad o conveniencia de las propuestas; presenta la evidencia para que ciudadanos y periodistas puedan realizar su propia evaluación.
\end{quote}

\section{Principio de diseño final}

\begin{center}
\Large
\textbf{La IA organiza la evidencia.}\\[0.3cm]
\textbf{Los datos aportan el contexto.}\\[0.3cm]
\textbf{Los cálculos muestran las diferencias.}\\[0.3cm]
\textbf{El humano toma la decisión.}
\end{center}

\end{document}
