"use client";

import { FormEvent, useEffect, useMemo, useState, useRef } from "react";
import { ArrowLeft, Check, ChevronDown, LoaderCircle, Search, ShieldCheck, Anchor } from "lucide-react";
import Link from "next/link";
import AnclaConfianza from "@/components/AnclaConfianza";

type Proceso = { id: string; nombre: string; cantones?: string[] };
type Candidato = {
  id: string; nombre: string; dignidad: string; territorio?: string;
  organizacion_politica?: string; fuente?: string;
};
type Promesa = {
  id?: string; candidato?: string; categoria?: string; accion?: string; objeto?: string;
  propuesta?: string; texto_original?: string; pagina_o_seccion?: string | number;
  enlace_documento?: string; nombre_candidato?: string;
};
type Grupo = { ambito: string; propuestas_por_candidato: { candidato: string; propuestas: Promesa[] }[] };

const api = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`/backend${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? `Error ${response.status}`);
  }
  return response.json() as Promise<T>;
};

const citaTextual = (item: Promesa) => item.texto_original?.trim() || item.propuesta?.trim() || "No hay texto original disponible.";

function EnlaceFuente({ item }: { item: Promesa }) {
  if (!item.enlace_documento) return <span className="text-[10px] font-mono text-gray-600">Fuente pública no disponible</span>;
  return <a href={item.enlace_documento} target="_blank" rel="noreferrer" className="text-[10px] font-mono text-accent hover:underline">Ver PDF fuente · pág. {item.pagina_o_seccion ?? "s/d"}</a>;
}

function TablaComparacion({ grupos, candidatos }: { grupos: Grupo[]; candidatos: Candidato[] }) {
  if (!grupos.length) return <p className="text-sm text-gray-500">No se encontraron ámbitos para esta vista.</p>;
  return (
    <div className="overflow-x-auto mt-8 pb-8">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-white/10 text-[10px] uppercase tracking-[.18em] text-gray-400">
          <tr><th className="py-4 pr-6 font-medium">Ámbito</th>{candidatos.map(c => <th className="py-4 px-6 font-medium" key={c.id}>{c.nombre}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {grupos.map((grupo, index) => (
            <tr key={`${grupo.ambito}-${index}`} className="align-top hover:bg-white/[.025] transition-colors">
              <td className="py-6 pr-6 text-accent font-mono text-[10px] tracking-widest">{grupo.ambito}</td>
              {candidatos.map(candidato => {
                const items = grupo.propuestas_por_candidato.find(item => item.candidato === candidato.id)?.propuestas ?? [];
                return <td className="p-4 leading-relaxed text-gray-300" key={candidato.id}>
                  {items.length ? items.map((item, itemIndex) => <div className="mb-3 last:mb-0" key={`${item.id}-${itemIndex}`}>
                    <blockquote className="whitespace-pre-wrap border-l border-white/20 pl-3">{citaTextual(item)}</blockquote>
                    <p className="mt-2"><EnlaceFuente item={item} /></p>
                  </div>) : <span className="text-gray-600">Sin propuesta relacionada</span>}
                </td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ComparacionPage() {
  const [procesos, setProcesos] = useState<Proceso[]>([]);
  const [cantonesDisponibles, setCantonesDisponibles] = useState<string[]>([]);
  const [procesoId, setProcesoId] = useState("");
  const [canton, setCanton] = useState("");
  const [candidatos, setCandidatos] = useState<Candidato[]>([]);
  const [seleccionados, setSeleccionados] = useState<string[]>([]);
  const [estado, setEstado] = useState("Selecciona dos candidaturas para comparar sus planes públicos.");
  const [procesando, setProcesando] = useState(false);
  const [vista, setVista] = useState<"similitudes" | "diferencias" | null>(null);
  const [grupos, setGrupos] = useState<Grupo[]>([]);
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState("");
  const [evidencias, setEvidencias] = useState<Promesa[]>([]);
  const [promesaAncla, setPromesaAncla] = useState<Promesa | null>(null);
  const anclaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (promesaAncla && anclaRef.current) {
      setTimeout(() => {
        anclaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }, [promesaAncla]);

  const proceso = useMemo(() => procesos.find(item => item.id === procesoId), [procesos, procesoId]);
  const candidatosSeleccionados = useMemo(() => candidatos.filter(c => seleccionados.includes(c.id)), [candidatos, seleccionados]);
  const cantones = cantonesDisponibles.length ? cantonesDisponibles : (proceso?.cantones ?? (canton ? [canton] : []));

  useEffect(() => {
    api<Proceso[]>("/procesos-electorales")
      .then(data => {
        setProcesos(data);
        const municipal = data.find(item => item.cantones?.length) ?? data[0];
        if (municipal) { setProcesoId(municipal.id); setCanton(municipal.cantones?.[0] ?? ""); }
      })
      .catch(error => setEstado(`No se pudo conectar al backend: ${error.message}`));
  }, []);

  useEffect(() => {
    api<string[]>("/cantones")
      .then(setCantonesDisponibles)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!procesoId || !canton) return;
    setSeleccionados([]); setGrupos([]); setVista(null); setRespuesta("");
    api<Candidato[]>(`/procesos-electorales/${encodeURIComponent(procesoId)}/candidaturas?canton=${encodeURIComponent(canton)}`)
      .then(setCandidatos)
      .catch(error => { setCandidatos([]); setEstado(`No se pudieron cargar las candidaturas: ${error.message}`); });
  }, [procesoId, canton]);

  const cambiarProceso = (id: string) => {
    setProcesoId(id);
    const siguiente = procesos.find(item => item.id === id);
    setCanton(siguiente?.cantones?.[0] ?? "");
  };

  const alternarCandidato = (id: string) => {
    setSeleccionados(actual => actual.includes(id) ? actual.filter(item => item !== id) : actual.length < 2 ? [...actual, id] : actual);
  };

  const esperarProcesamiento = async (trabajoId: string) => {
    for (let intento = 0; intento < 180; intento += 1) {
      const trabajo = await api<{ estado: string; mensaje: string }>(`/procesamientos/${trabajoId}`);
      setEstado(trabajo.mensaje);
      if (trabajo.estado === "completado") return;
      if (trabajo.estado === "fallido") throw new Error(trabajo.mensaje);
      await new Promise(resolve => setTimeout(resolve, 1800));
    }
    throw new Error("El procesamiento está tomando más de lo esperado. Revisa la consola del backend.");
  };

  const procesar = async () => {
    if (seleccionados.length !== 2) { setEstado("Selecciona exactamente dos candidaturas."); return; }
    setProcesando(true); setEstado("Descargando y extrayendo evidencia de los planes públicos…");
    try {
      const trabajo = await api<{ trabajo_id: string }>(`/procesos-electorales/${encodeURIComponent(procesoId)}/procesar-planes`, {
        method: "POST", body: JSON.stringify({ candidato_ids: seleccionados, max_fragmentos: 40 }),
      });
      await esperarProcesamiento(trabajo.trabajo_id);
      setEstado("Planes listos. Elige ámbitos compartidos o diferencias para ver la tabla.");
    } catch (error) { setEstado(error instanceof Error ? error.message : "Falló el procesamiento."); }
    finally { setProcesando(false); }
  };

  const cargarComparacion = async (tipo: "similitudes" | "diferencias") => {
    if (seleccionados.length !== 2) { setEstado("Procesa y selecciona dos candidaturas primero."); return; }
    try {
      const resultado = await api<{ similitudes: Grupo[]; diferencias: Grupo[] }>("/comparaciones", {
        method: "POST", body: JSON.stringify({ candidato_ids: seleccionados }),
      });
      setVista(tipo); setGrupos(resultado[tipo]);
      setEstado(tipo === "similitudes" ? "Ámbitos compartidos: no implica que las propuestas sean idénticas." : "Ámbitos con propuestas de una sola candidatura.");
    } catch (error) { setEstado(error instanceof Error ? error.message : "No se pudo generar la comparación."); }
  };

  const preguntar = async (event: FormEvent) => {
    event.preventDefault();
    if (!pregunta.trim()) return;
    setPromesaAncla(null); // Limpiar ancla previa
    try {
      const resultado = await api<{ respuesta: string; evidencias: Promesa[] }>("/preguntas", {
        method: "POST", body: JSON.stringify({ pregunta, candidato_ids: seleccionados }),
      });
      setRespuesta(resultado.respuesta); setEvidencias(resultado.evidencias);
    } catch (error) { setRespuesta(error instanceof Error ? error.message : "No se pudo responder la pregunta."); setEvidencias([]); }
  };

  return <main className="min-h-screen overflow-y-auto bg-dark bg-grid text-white px-5 py-10 md:px-12 md:py-14">
    <div className="mx-auto max-w-7xl">
      <Link href="/" className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[.25em] text-gray-500 hover:text-white"><ArrowLeft className="h-3 w-3" /> Inicio</Link>
      <header className="mt-10 mb-10 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div><p className="font-mono text-xs uppercase tracking-[.25em] text-accent">CondorLens · Elecciones seccionales</p><h1 className="mt-3 text-4xl font-light md:text-6xl">Comparador de <span className="text-accent">planes</span></h1><p className="mt-4 max-w-2xl text-gray-400">Compara candidaturas a alcaldía del mismo cantón con evidencia trazable de sus planes públicos.</p></div>
        <div className="flex items-center gap-2 text-xs text-gray-400"><ShieldCheck className="h-4 w-4 text-accent" /> Sin recomendaciones ni evaluación de candidaturas.</div>
      </header>

      {/* Selection Area - Editorial minimal style */}
      <section className="mb-12">
        <div className="flex flex-col md:flex-row gap-8 md:gap-24 border-b border-white/10 pb-10">
          <div className="flex-1 group">
            <label className="block text-[10px] font-mono uppercase tracking-[0.3em] text-accent mb-4 opacity-70 group-hover:opacity-100 transition-opacity">Proceso electoral</label>
            <div className="relative">
              <select value={procesoId} onChange={event => cambiarProceso(event.target.value)} className="w-full bg-transparent text-2xl md:text-4xl font-light text-white outline-none appearance-none cursor-pointer border-b border-transparent focus:border-white/20 pb-3 pr-10 transition-colors">
                {procesos.map(item => <option className="bg-dark text-lg" value={item.id} key={item.id}>{item.nombre}</option>)}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 text-gray-500 pointer-events-none transition-colors group-hover:text-white" />
            </div>
          </div>
          <div className="flex-1 group">
            <label className="block text-[10px] font-mono uppercase tracking-[0.3em] text-accent mb-4 opacity-70 group-hover:opacity-100 transition-opacity">Cantón</label>
            <div className="relative">
              <select value={canton} onChange={event => setCanton(event.target.value)} className="w-full bg-transparent text-2xl md:text-4xl font-light text-white outline-none appearance-none cursor-pointer border-b border-transparent focus:border-white/20 pb-3 pr-10 transition-colors">
                {cantones.map(item => <option className="bg-dark text-lg" value={item} key={item}>{item}</option>)}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 text-gray-500 pointer-events-none transition-colors group-hover:text-white" />
            </div>
          </div>
        </div>
        <p className="mt-6 text-sm text-gray-400 font-light">Elige dos candidaturas a alcaldía para una comparación municipal directa.</p>
      </section>

      <section className="mt-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4"><h2 className="text-xl">Candidaturas disponibles <span className="text-sm text-gray-500">({seleccionados.length}/2)</span></h2>
          <button onClick={procesar} disabled={procesando || seleccionados.length !== 2} className="group relative px-6 py-4 bg-white text-dark rounded-full overflow-hidden disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer">
            <div className="absolute inset-0 w-full h-full bg-accent -translate-x-full group-hover:translate-x-0 transition-transform duration-700 ease-[0.16,1,0.3,1] group-disabled:hidden"></div>
            <span className="relative z-10 text-[10px] font-bold tracking-[0.2em] uppercase group-hover:text-white transition-colors duration-700 flex items-center gap-3">
              {procesando && <LoaderCircle className="h-4 w-4 animate-spin" />}
              {procesando ? "Procesando…" : "Procesar planes seleccionados"}
            </span>
          </button>
        </div>
        <p className="mb-5 text-sm text-gray-400">{estado}</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {candidatos.map(candidato => { const activo = seleccionados.includes(candidato.id); return <button key={candidato.id} onClick={() => alternarCandidato(candidato.id)} className={`rounded-2xl border p-5 text-left transition ${activo ? "border-accent bg-accent/10" : "border-white/10 bg-white/[.02] hover:border-white/30"}`}>
            <div className="flex items-start justify-between gap-3"><div><h3 className="font-medium">{candidato.nombre}</h3><p className="mt-1 text-xs text-gray-400">{candidato.dignidad}</p></div><span className={`flex h-5 w-5 items-center justify-center rounded border ${activo ? "border-accent bg-accent text-dark" : "border-gray-600"}`}>{activo && <Check className="h-3 w-3" />}</span></div>
            <p className="mt-4 text-xs leading-relaxed text-gray-500">{candidato.organizacion_politica ?? "Plan público disponible"}</p>
          </button>; })}
        </div>
      </section>

      <section className="mt-16 border-t border-white/10 pt-16 grid gap-16 xl:grid-cols-[1.7fr_1fr]">
        <div className="flex flex-col">
          <div className="flex flex-col gap-6 md:flex-row md:items-end justify-between mb-10">
            <div>
              <h2 className="text-3xl md:text-4xl font-light">Comparación por ámbitos</h2>
              <p className="mt-3 text-[10px] font-mono uppercase tracking-[0.2em] text-gray-500">Cada celda conserva la página de la evidencia.</p>
            </div>
            <div className="flex gap-8 border-b border-white/10 pb-2">
              <button onClick={() => cargarComparacion("similitudes")} className={`text-[10px] font-mono uppercase tracking-[0.3em] transition-all duration-300 relative pb-2 ${vista === 'similitudes' ? 'text-accent' : 'text-gray-500 hover:text-white'}`}>
                Ámbitos compartidos
                {vista === 'similitudes' && <div className="absolute -bottom-[1px] left-0 w-full h-[1px] bg-accent" />}
              </button>
              <button onClick={() => cargarComparacion("diferencias")} className={`text-[10px] font-mono uppercase tracking-[0.3em] transition-all duration-300 relative pb-2 ${vista === 'diferencias' ? 'text-white' : 'text-gray-500 hover:text-white'}`}>
                Diferencias
                {vista === 'diferencias' && <div className="absolute -bottom-[1px] left-0 w-full h-[1px] bg-white" />}
              </button>
            </div>
          </div>
          {vista && <div className="mt-5"><p className="mb-3 font-mono text-[10px] uppercase tracking-[0.2em] text-gray-500">{vista === "similitudes" ? "Propuestas relacionadas por ámbito" : "Ámbitos no compartidos"}</p><TablaComparacion grupos={grupos} candidatos={candidatosSeleccionados} /></div>}
        {/* Pregunta a los planes */}
        <aside className="flex flex-col">
          <h2 className="text-[10px] font-mono uppercase tracking-[0.3em] text-accent mb-6">Pregunta a los planes</h2>
          <p className="text-sm text-gray-500 font-light mb-10 max-w-sm">Pregunta sólo por propuestas de los planes procesados. Las consultas fuera de ese ámbito se bloquean de forma segura.</p>
          
          <form onSubmit={preguntar} className="flex flex-col relative group">
            <div className="relative w-full min-h-[15vh]">
              <textarea value={pregunta} onChange={event => setPregunta(event.target.value)} maxLength={600} placeholder="Ej. ¿Qué proponen sobre seguridad y espacio público?" spellCheck="false" className="w-full h-full bg-transparent resize-none focus:outline-none text-xl md:text-2xl font-light leading-[1.4] placeholder-white/20 text-white/90" />
              <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/10 group-focus-within:bg-white/40 transition-colors duration-700"></div>
              <div className="absolute -bottom-6 right-0 text-[10px] font-mono text-gray-600 tracking-widest">{pregunta.length} / 600</div>
            </div>
            
            <div className="mt-12 flex justify-end">
              <button disabled={!pregunta.trim()} className="group relative px-6 py-4 bg-white text-dark rounded-full overflow-hidden disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer">
                <div className="absolute inset-0 w-full h-full bg-accent -translate-x-full group-hover:translate-x-0 transition-transform duration-700 ease-[0.16,1,0.3,1]"></div>
                <span className="relative z-10 text-[10px] font-bold tracking-[0.2em] uppercase group-hover:text-white transition-colors duration-700 flex items-center gap-3"><Search className="w-3 h-3" /> Preguntar con evidencia</span>
              </button>
            </div>
          </form>
          
          {respuesta && <div className="mt-16 pt-10 border-t border-white/5"><h3 className="text-[10px] font-mono uppercase tracking-[0.3em] text-accent mb-6">Fragmentos textuales recuperados</h3><p className="whitespace-pre-wrap text-xl md:text-2xl font-light leading-relaxed text-white/90 mb-10">{respuesta}</p>{evidencias.length > 0 && <div className="w-full overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm border-t border-white/10"><thead className="text-[10px] font-mono uppercase tracking-[0.3em] text-gray-500"><tr><th className="py-6 pr-4 font-normal w-1/4">Candidatura</th><th className="py-6 px-4 font-normal w-1/2">Cita textual del plan</th><th className="py-6 pl-4 font-normal text-right">Fuente</th></tr></thead><tbody className="divide-y divide-white/5">{evidencias.map((item, index) => <tr key={`${item.id}-${index}`} className="group hover:bg-white/[0.02] transition-colors"><td className="py-6 pr-4 text-white font-medium align-top">{item.nombre_candidato ?? item.candidato}</td><td className="py-6 px-4 text-gray-400 font-light text-sm leading-relaxed align-top whitespace-pre-wrap">{citaTextual(item)}<div className="mt-3"><button onClick={() => setPromesaAncla(item)} className="inline-flex items-center gap-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest text-amber-400 transition-colors hover:bg-amber-500/20"><Anchor className="h-3 w-3" /> Ver contexto histórico</button></div></td><td className="py-6 pl-4 text-gray-500 align-top text-right"><EnlaceFuente item={item} /></td></tr>)}</tbody></table></div>}</div>}
        </aside>
      </section>

      <div ref={anclaRef}>
        <AnclaConfianza
          candidatoIds={seleccionados}
          promesa={promesaAncla}
        />
      </div>
    </div>
  </main>;
}
