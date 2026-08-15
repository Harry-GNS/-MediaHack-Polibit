"use client";

import { useEffect, useState } from "react";
import { Anchor } from "lucide-react";

type Antecedente = {
  candidato: string;
  proceso_electoral_id?: string | null;
  categoria?: string;
  accion?: string;
  objeto?: string;
  cantidad?: number | null;
  unidad?: string | null;
  plazo?: string | null;
  texto: string;
  fuente?: string;
  fuente_url?: string | null;
};

type AnclaData = {
  total_antecedentes: number;
  promedio_historico_cantidad: number | null;
  antecedentes: Antecedente[];
  nota: string;
};

interface Props {
  candidatoIds: string[];
  promesa: { categoria?: string; objeto?: string; texto_original?: string } | null;
}

export default function AnclaConfianza({ candidatoIds, promesa }: Props) {
  const [data, setData] = useState<AnclaData | null>(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (!promesa) return;

    // Cuando viene de una búsqueda libre, puede no tener categoría/objeto, así que usamos el texto
    const categoria = promesa.categoria ?? "";
    const objeto = promesa.objeto ?? promesa.texto_original ?? "";

    const params = new URLSearchParams();
    if (categoria) params.append("categoria", categoria);
    if (objeto) params.append("objeto", objeto);
    candidatoIds.forEach(id => params.append("candidato_ids", id));

    setCargando(true);
    fetch(`/backend/ancla?${params.toString()}`)
      .then(res => res.json())
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setCargando(false));
  }, [promesa, candidatoIds]);

  if (!promesa || (!cargando && (!data || data.total_antecedentes === 0))) return null;

  const propuesta = (a: Antecedente) => {
    const partes = [
      a.accion && a.accion.toLowerCase() !== "no_especificado" ? a.accion : null,
      a.objeto && a.objeto.toLowerCase() !== "no_especificado" ? a.objeto : null,
      a.cantidad != null ? `${a.cantidad}${a.unidad ? ` ${a.unidad}` : ""}` : null,
    ].filter(Boolean);
    const resultado = partes.join(" ").trim();
    if (!resultado || resultado.toLowerCase() === "no_especificado") return null;
    // Si el texto ya comienza con este resumen, no duplicarlo
    if (a.texto.toLowerCase().startsWith(resultado.toLowerCase())) return null;
    return resultado;
  };

  return (
    <section className="mt-16 border-t border-amber-500/20 pt-12">
      <div className="mb-8 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div className="flex items-center gap-3">
          <Anchor className="h-5 w-5 text-amber-400 shrink-0" />
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[.25em] text-amber-400">
              Ancla de Confianza
            </p>
            <h2 className="mt-1 text-2xl font-light md:text-3xl">
              Contexto <span className="text-amber-400">historico</span>
            </h2>
          </div>
        </div>
        <p className="max-w-md text-xs leading-relaxed text-gray-500">
          {data?.nota ?? "Cargando antecedentes documentados..."}
        </p>
      </div>

      {cargando && (
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span className="inline-block h-3 w-3 animate-spin rounded-full border border-amber-400 border-t-transparent" />
          Buscando promesas similares en planes publicos anteriores...
        </div>
      )}

      {!cargando && data && data.total_antecedentes > 0 && (
        <>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-5">
              <h3 className="font-mono text-[10px] uppercase tracking-widest text-gray-500">Antecedentes</h3>
              <p className="mt-2 text-3xl font-light text-amber-500">{data.total_antecedentes}</p>
              <p className="mt-1 text-xs text-gray-400">promesas similares encontradas</p>
            </div>
            {data.promedio_historico_cantidad !== null && (
              <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-gray-500">Promedio Histórico</h3>
                <p className="mt-2 text-3xl font-light text-white">{data.promedio_historico_cantidad}</p>
                <p className="mt-1 text-xs text-gray-400">unidades prometidas en promedio</p>
              </div>
            )}
          </div>

          <div className="mt-6 flex flex-col gap-4">
            {data.antecedentes.map((a, i) => (
              <div key={i} className="group relative rounded-2xl border border-white/10 bg-white/[.02] p-5 transition-colors hover:border-amber-500/50 hover:bg-white/5">
                <div className="absolute -left-2.5 top-8 flex h-5 w-5 items-center justify-center rounded-full border border-amber-500/30 bg-black">
                  <div className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                </div>

                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="rounded bg-cyan-900/30 px-2 py-0.5 font-mono text-[9px] font-bold tracking-wider text-cyan-400 uppercase">
                        {a.categoria && a.categoria.toLowerCase() !== "no_especificado" ? a.categoria : "Plan Oficial"}
                      </span>
                      {a.plazo && <span className="font-mono text-[9px] tracking-widest text-gray-500 uppercase">Plazo: {a.plazo}</span>}
                    </div>
                    
                    <p className="mt-4 text-sm leading-relaxed text-gray-300">
                      {propuesta(a) && <span className="text-white font-medium">{propuesta(a)} </span>}
                      {a.texto}
                    </p>
                  </div>

                  <div className="flex flex-col items-end gap-1 text-right sm:min-w-[140px]">
                    <p className="text-sm font-medium text-white">{a.candidato}</p>
                    <p className="font-mono text-[9px] text-gray-500">{a.proceso_electoral_id}</p>
                    {a.fuente && (
                      <div className="mt-3">
                        {a.fuente_url ? (
                          <a href={a.fuente_url} target="_blank" rel="noopener noreferrer" className="text-[10px] font-mono tracking-widest uppercase text-cyan-400 hover:underline">
                            Ver fuente
                          </a>
                        ) : (
                          <span className="text-[9px] text-gray-500">{a.fuente}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
