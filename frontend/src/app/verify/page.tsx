"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, X, LoaderCircle, CheckCircle, XCircle, AlertTriangle, ShieldAlert, ChevronRight } from 'lucide-react';

type Tab = 'text' | 'links';

type ResultadoValidacion = {
  estado: 'concordante' | 'discrepante' | 'no_encontrado';
  porcentaje: number;
  diferencias: string | null;
  fuente_url: string;
  valor_en_fuente: string | null;
  alerta: string;
};

const esUrlHttp = (valor: string) => /^https?:\/\/[^\s]+$/i.test(valor.trim());

export default function VerifyPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [sources, setSources] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ResultadoValidacion[] | null>(null);

  const handleAddSource = () => {
    if (sources.length < 5) setSources([...sources, '']);
  };

  const handleSourceChange = (index: number, value: string) => {
    const newSources = [...sources];
    newSources[index] = value;
    setSources(newSources);
  };

  const handleRemoveSource = (index: number) => {
    const newSources = sources.filter((_, i) => i !== index);
    setSources(newSources.length ? newSources : ['']);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const fuentesIngresadas = sources.filter(s => s.trim() !== '');
    const validSources = fuentesIngresadas.filter(esUrlHttp);
    if (!prompt.trim() || validSources.length === 0 || validSources.length !== fuentesIngresadas.length) {
      setError("Por favor ingresa el dato a comprobar y al menos una URL válida.");
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const res = await fetch('/backend/validar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: prompt.trim().slice(0, 8000), fuentes: validSources })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || `Error ${res.status}: Falló la conexión con el auditor.`);
      }

      const data: unknown = await res.json();
      if (!Array.isArray(data)) throw new Error('El auditor devolvió una respuesta no válida.');
      setResults(data as ResultadoValidacion[]);
      
      // Auto-scroll to results
      setTimeout(() => {
        document.getElementById('audit-results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ocurrió un error inesperado al procesar la auditoría.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.main 
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -30 }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      className="min-h-screen bg-dark text-white pt-32 pb-24 px-8 md:px-16 lg:px-24 flex flex-col relative z-10"
    >
      {/* Top Navigation */}
      <div className="w-full flex items-center justify-between mb-16">
        <button 
          onClick={() => router.back()} 
          className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-colors w-max"
        >
          <ArrowLeft className="w-3 h-3" /> Volver
        </button>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSubmit} className="w-full flex flex-col flex-1 gap-16 lg:gap-24">
        
        {/* Sección 1: Evidencia */}
        <div className="w-full flex flex-col">
          <h3 className="text-[10px] font-mono tracking-[0.3em] text-gray-500 uppercase mb-8">1. Dato a comprobar</h3>
          <div className="relative group w-full min-h-[20vh] lg:min-h-[25vh]">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value.slice(0, 8000))}
              placeholder="Pega la declaración, noticia o frase aquí..."
              spellCheck="false"
              className="w-full h-full bg-transparent resize-none focus:outline-none text-2xl md:text-4xl lg:text-5xl font-light font-playfair leading-[1.2] placeholder-white/10 text-white/90"
            />
            <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/10 group-focus-within:bg-white/40 transition-colors duration-700"></div>
            <div className="absolute -bottom-8 right-0 text-[10px] font-mono text-gray-600 tracking-widest">
              {prompt.length} / 8 000
            </div>
          </div>
        </div>

        {/* Sección 2: Fuentes */}
        <div className="w-full flex flex-col">
          <div className="flex items-end justify-between border-b border-white/5 pb-4 mb-8">
            <h3 className="text-[10px] font-mono tracking-[0.3em] text-gray-500 uppercase">2. URLs de contraste (Fuentes)</h3>
            <span className="text-[10px] text-gray-600 font-mono tracking-widest">{sources.length}/5</span>
          </div>
          
          <div className="space-y-6">
            {sources.map((source, idx) => (
              <div key={idx} className="flex items-center gap-6 group relative">
                <span className="text-xs font-mono text-accent opacity-50 group-focus-within:opacity-100 transition-opacity">0{idx + 1}.</span>
                <input
                  type="url"
                  value={source}
                  onChange={(e) => handleSourceChange(idx, e.target.value)}
                  placeholder="https://"
                  className="flex-1 bg-transparent border-none focus:outline-none text-lg md:text-2xl font-light text-gray-300 placeholder-white/10 group-hover:placeholder-white/20 transition-colors pb-2"
                />
                {sources.length > 1 && (
                  <button type="button" onClick={() => handleRemoveSource(idx)} className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all absolute right-0">
                    <X className="w-5 h-5" />
                  </button>
                )}
                <div className="absolute bottom-0 left-8 right-0 h-[1px] bg-transparent group-focus-within:bg-white/10 transition-colors duration-500"></div>
              </div>
            ))}
          </div>

          <button 
            type="button" 
            onClick={handleAddSource} 
            disabled={sources.length >= 5 || loading}
            className="mt-8 flex items-center gap-3 text-[10px] font-mono tracking-[0.2em] text-gray-500 hover:text-white transition-colors disabled:opacity-30 uppercase w-max"
          >
            <span className="w-6 h-6 rounded-full border border-gray-700 flex items-center justify-center"><Plus className="w-3 h-3" /></span> 
            Agregar nueva fuente
          </button>
        </div>

        {/* Submit Button - Always visible at the bottom */}
        <div className="mt-8 flex items-center justify-between">
          <div className="flex-1">
            {error && (
              <p className="text-red-400 text-xs font-mono tracking-widest">{error}</p>
            )}
          </div>
          <button 
            type="submit" 
            disabled={!prompt.trim() || loading || sources.every(s => !s.trim())}
            className="group relative px-8 py-4 bg-white text-dark rounded-full overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <div className="absolute inset-0 w-full h-full bg-accent -translate-x-full group-hover:translate-x-0 transition-transform duration-700 ease-[0.16,1,0.3,1] group-disabled:hidden"></div>
            <span className="relative z-10 text-xs font-bold tracking-[0.2em] uppercase group-hover:text-white transition-colors duration-700 flex items-center gap-3">
              {loading && <LoaderCircle className="w-4 h-4 animate-spin" />}
              {loading ? "Analizando fuentes..." : "Ejecutar Auditoría"}
            </span>
          </button>
        </div>
      </form>

      {/* Results Section */}
      <AnimatePresence>
        {results && results.length > 0 && (
          <motion.div 
            id="audit-results"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="w-full mt-24 pt-24 border-t border-white/10 flex flex-col gap-12"
          >
            <div className="flex flex-col gap-4">
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-light">
                Veredicto de <span className="text-accent font-black">Auditoría</span>
              </h2>
              <p className="text-gray-400 font-light max-w-2xl">
                Análisis algorítmico cruzado contra las fuentes proporcionadas. Cada tarjeta representa el contraste con una URL individual.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {results.map((res, i) => (
                <div key={i} className="p-8 md:p-10 border border-white/10 bg-white/[0.02] hover:bg-white/[0.04] transition-colors rounded-2xl flex flex-col xl:flex-row gap-8 lg:gap-16">
                  
                  {/* Left Column: Verdict */}
                  <div className="flex-shrink-0 xl:w-72">
                    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-[10px] font-mono uppercase tracking-widest mb-6 ${
                      res.estado === 'concordante' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                      res.estado === 'discrepante' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                      'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                    }`}>
                      {res.estado === 'concordante' && <CheckCircle className="w-3 h-3" />}
                      {res.estado === 'discrepante' && <XCircle className="w-3 h-3" />}
                      {res.estado === 'no_encontrado' && <AlertTriangle className="w-3 h-3" />}
                      {res.estado.replace('_', ' ')}
                    </div>

                    <div className="space-y-1">
                      <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-gray-500">
                        Nivel de certeza
                      </p>
                      <p className="text-5xl font-light text-white">
                        {res.porcentaje}<span className="text-2xl text-gray-500">%</span>
                      </p>
                    </div>
                  </div>

                  {/* Right Column: Evidence */}
                  <div className="flex-1 flex flex-col justify-center">
                    <div className="mb-6 flex items-start gap-3">
                      <ShieldAlert className="w-5 h-5 text-accent flex-shrink-0 mt-1" />
                      <p className="text-xl md:text-2xl font-light leading-relaxed text-gray-200">
                        {res.alerta}
                      </p>
                    </div>

                    {res.diferencias && (
                      <div className="mb-6">
                        <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-red-400 mb-2">Diferencias detectadas</p>
                        <p className="text-sm text-gray-400 font-light leading-relaxed">{res.diferencias}</p>
                      </div>
                    )}

                    {res.valor_en_fuente && (
                      <div className="mt-4 border-l border-white/20 pl-6 py-2">
                        <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-gray-500 mb-3">
                          Cita literal de la fuente
                        </p>
                        <blockquote className="text-sm text-gray-300 font-mono italic leading-relaxed">
                          "{res.valor_en_fuente}"
                        </blockquote>
                      </div>
                    )}

                    {res.fuente_url && (
                      <div className="mt-8 pt-6 border-t border-white/5">
                        <a 
                          href={res.fuente_url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-accent hover:text-white transition-colors"
                        >
                          Ver fuente original <ChevronRight className="w-3 h-3" />
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.main>
  );
}
