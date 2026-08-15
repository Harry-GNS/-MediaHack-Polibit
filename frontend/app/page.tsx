"use client";

import { useState } from "react";
import { CheckCircle, AlertTriangle, XCircle, Plus, Trash2, Loader2, ExternalLink } from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

interface DatoEstadistico {
  texto_original: string;
  valor: number;
  unidad: string;
  contexto: string;
}

interface ResultadoValidacion {
  dato: DatoEstadistico;
  estado: "concordante" | "discrepante" | "no_encontrado";
  fuente_url: string | null;
  valor_en_fuente: string | null;
  alerta: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function EstadoBadge({ estado }: { estado: ResultadoValidacion["estado"] }) {
  if (estado === "concordante")
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
        <CheckCircle size={14} /> Concordante
      </span>
    );
  if (estado === "discrepante")
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
        <AlertTriangle size={14} /> Discrepante
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold bg-red-500/15 text-red-400 border border-red-500/30">
      <XCircle size={14} /> No encontrado
    </span>
  );
}

function tarjetaColor(estado: ResultadoValidacion["estado"]) {
  if (estado === "concordante") return "border-emerald-500/40 bg-emerald-950/20";
  if (estado === "discrepante") return "border-amber-500/40 bg-amber-950/20";
  return "border-red-500/40 bg-red-950/20";
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ValidadorPage() {
  const [texto, setTexto] = useState("");
  const [fuentes, setFuentes] = useState<string[]>([""]);
  const [resultados, setResultados] = useState<ResultadoValidacion[] | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const agregarFuente = () => setFuentes((prev) => [...prev, ""]);
  const eliminarFuente = (i: number) => setFuentes((prev) => prev.filter((_, idx) => idx !== i));
  const actualizarFuente = (i: number, val: string) =>
    setFuentes((prev) => prev.map((f, idx) => (idx === i ? val : f)));

  const fuentesValidas = fuentes.filter((f) => f.trim().startsWith("http"));

  async function validar() {
    if (!texto.trim() || fuentesValidas.length === 0) return;
    setCargando(true);
    setError(null);
    setResultados(null);

    try {
      const res = await fetch("/api/validar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto, fuentes: fuentesValidas }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error desconocido");
      setResultados(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  }

  // Resumen
  const concordantes = resultados?.filter((r) => r.estado === "concordante").length ?? 0;
  const total = resultados?.length ?? 0;

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100 font-sans">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            EE
          </div>
          <div>
            <h1 className="font-semibold text-zinc-100 leading-tight">Evidencia Electoral</h1>
            <p className="text-xs text-zinc-500">Validador de datos estadísticos · Sin veredictos, solo evidencia</p>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Texto a validar */}
        <section className="space-y-3">
          <label htmlFor="texto-validar" className="block text-sm font-medium text-zinc-300">
            Texto a validar
          </label>
          <textarea
            id="texto-validar"
            rows={7}
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Pega aquí el texto que contiene datos estadísticos o afirmaciones numéricas que deseas verificar…"
            className="w-full rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 resize-none transition"
          />
        </section>

        {/* Fuentes */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-zinc-300">Fuentes confiables</label>
            <button
              id="btn-agregar-fuente"
              onClick={agregarFuente}
              className="inline-flex items-center gap-1.5 text-xs text-violet-400 hover:text-violet-300 transition"
            >
              <Plus size={13} /> Agregar fuente
            </button>
          </div>
          <div className="space-y-2">
            {fuentes.map((f, i) => (
              <div key={i} className="flex gap-2">
                <input
                  id={`fuente-${i}`}
                  type="url"
                  value={f}
                  onChange={(e) => actualizarFuente(i, e.target.value)}
                  placeholder={`https://www.fuente-${i + 1}.com/articulo`}
                  className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition"
                />
                {fuentes.length > 1 && (
                  <button
                    id={`btn-eliminar-fuente-${i}`}
                    onClick={() => eliminarFuente(i)}
                    className="p-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-950/30 transition"
                    aria-label="Eliminar fuente"
                  >
                    <Trash2 size={15} />
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-zinc-600">
            {fuentesValidas.length} fuente{fuentesValidas.length !== 1 ? "s" : ""} válida{fuentesValidas.length !== 1 ? "s" : ""}
          </p>
        </section>

        {/* Botón validar */}
        <button
          id="btn-validar"
          onClick={validar}
          disabled={cargando || !texto.trim() || fuentesValidas.length === 0}
          className="w-full py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
        >
          {cargando ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Validando…
            </>
          ) : (
            "Validar datos"
          )}
        </button>

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-500/40 bg-red-950/20 px-4 py-3 text-sm text-red-400">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Resultados */}
        {resultados && resultados.length > 0 && (
          <section className="space-y-5">
            {/* Resumen */}
            <div className="rounded-xl border border-zinc-700 bg-zinc-900 p-4 space-y-2">
              <p className="text-sm font-medium text-zinc-300">
                Resumen: <span className="text-emerald-400 font-semibold">{concordantes}</span> de{" "}
                <span className="font-semibold">{total}</span> dato{total !== 1 ? "s" : ""} concordante{concordantes !== 1 ? "s" : ""}
              </p>
              <div className="w-full h-2 rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-700"
                  style={{ width: total > 0 ? `${(concordantes / total) * 100}%` : "0%" }}
                />
              </div>
            </div>

            {/* Tarjetas por dato */}
            <div className="space-y-3">
              {resultados.map((r, i) => (
                <article
                  key={i}
                  id={`resultado-${i}`}
                  className={`rounded-xl border p-4 space-y-3 transition ${tarjetaColor(r.estado)}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-mono text-zinc-200 leading-snug">
                      📊 &ldquo;{r.dato.texto_original}&rdquo;
                    </p>
                    <EstadoBadge estado={r.estado} />
                  </div>

                  <p className="text-xs text-zinc-400 italic border-l-2 border-zinc-700 pl-3">
                    {r.dato.contexto}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-zinc-400">
                    {r.fuente_url && (
                      <a
                        href={r.fuente_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 hover:text-violet-400 transition truncate"
                      >
                        <ExternalLink size={11} />
                        {r.fuente_url}
                      </a>
                    )}
                    {r.valor_en_fuente && (
                      <span>
                        Fuente dice: <span className="text-zinc-200 font-medium">{r.valor_en_fuente}</span>
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-zinc-400 bg-zinc-800/60 rounded-lg px-3 py-2">
                    {r.alerta}
                  </p>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
