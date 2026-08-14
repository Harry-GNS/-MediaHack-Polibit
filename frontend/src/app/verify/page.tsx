"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Plus, X } from 'lucide-react';

export default function VerifyPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [sources, setSources] = useState<string[]>(['']);

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    // Simulate saving state. In a real app we'd use context or local storage.
    // For now, we just navigate to results.
    router.push('/results');
  };

  return (
    <motion.main 
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -30 }}
      transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
      className="min-h-screen bg-dark text-white pt-32 pb-24 px-8 md:px-16 lg:px-24 flex flex-col relative z-10"
    >
      <div className="w-full">
        <button 
          onClick={() => router.back()} 
          className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-colors mb-16 w-max"
        >
          <ArrowLeft className="w-3 h-3" /> Volver
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 flex flex-col w-full h-full justify-between">
        
        {/* Giant Textarea */}
        <div className="flex-1 min-h-[40vh] relative group">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value.slice(0, 20000))}
            placeholder="Pega la evidencia aquí..."
            spellCheck="false"
            className="w-full h-full min-h-[40vh] bg-transparent resize-none focus:outline-none text-4xl md:text-6xl lg:text-[80px] font-light font-playfair leading-[1.1] placeholder-white/10 text-white/90"
          />
          <div className="absolute bottom-0 left-0 w-full h-[1px] bg-white/10 group-focus-within:bg-white/40 transition-colors duration-700"></div>
          <div className="absolute -bottom-8 right-0 text-[10px] font-mono text-gray-600 tracking-widest">
            {prompt.length} / 20 000
          </div>
        </div>

        {/* Sources Section - Awwwards minimalist style */}
        <div className="mt-20 md:mt-32 space-y-8">
          <div className="flex items-end justify-between border-b border-white/5 pb-4">
            <h3 className="text-[10px] font-mono tracking-[0.3em] text-gray-500 uppercase">Fuentes Confiables</h3>
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
                  className="flex-1 bg-transparent border-none focus:outline-none text-xl md:text-3xl font-light text-gray-300 placeholder-white/10 group-hover:placeholder-white/20 transition-colors pb-2"
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
            disabled={sources.length >= 5}
            className="mt-8 flex items-center gap-3 text-[10px] font-mono tracking-[0.2em] text-gray-500 hover:text-white transition-colors disabled:opacity-30 uppercase"
          >
            <span className="w-6 h-6 rounded-full border border-gray-700 flex items-center justify-center"><Plus className="w-3 h-3" /></span> 
            Agregar nueva fuente
          </button>
        </div>

        {/* Submit Button */}
        <div className="mt-32 pb-12 flex justify-end">
          <button 
            type="submit" 
            disabled={!prompt.trim()}
            className="group relative px-12 py-6 bg-white text-dark rounded-full overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <div className="absolute inset-0 w-full h-full bg-accent -translate-x-full group-hover:translate-x-0 transition-transform duration-700 ease-[0.16,1,0.3,1]"></div>
            <span className="relative z-10 text-xs font-bold tracking-[0.2em] uppercase group-hover:text-white transition-colors duration-700">
              Ejecutar Auditoría
            </span>
          </button>
        </div>
      </form>
    </motion.main>
  );
}
