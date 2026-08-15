"use client";

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Search, ArrowRight } from 'lucide-react';
import gsap from 'gsap';

// Components
import EvidenceCard from '@/components/EvidenceCard';
import AuditDrawer from '@/components/AuditDrawer';

export default function ResultsPage() {
  const router = useRouter();
  const [chatHistory, setChatHistory] = useState<{ type: 'user' | 'loader' | 'ai', text?: string }[]>([]);
  const [prompt, setPrompt] = useState('');
  const [drawerData, setDrawerData] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simulate incoming data from /verify
    setChatHistory([
      { type: 'user', text: "Según el informe de 2024, la tasa de alfabetización subió un 12% y la inversión en educación aumentó de manera histórica.\n\nFuentes a verificar:\nhttps://informe-2024.gob.ec" },
      { type: 'loader' }
    ]);

    const timer = setTimeout(() => {
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist.pop();
        return [...newHist, { type: 'ai' }];
      });
    }, 2500);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    gsap.to('.chat-msg:not(.animated)', {
      opacity: 1, y: 0, duration: 0.8, stagger: 0.2, ease: "power3.out",
      onComplete: function () {
        this.targets().forEach((el: any) => el.classList.add('animated'));
      }
    });
  }, [chatHistory]);

  const openDrawer = (id: string) => {
    const data = id === 'A01' ? {
      id: "A01",
      sourceText: "...nuestro compromiso es inquebrantable, por eso construiremos 300 unidades educativas durante nuestra administración...",
      highlightedText: "construiremos 300 unidades educativas",
      page: "42", metaReq: "75", metaHist: "12.5",
      calcMsg: "La meta requerida representa <strong class='font-medium text-white'>6× el promedio histórico registrado</strong> en los últimos 4 años.",
      barWidth: "100%", mult: "6×", isAlert: true
    } : {
      id: "B01",
      sourceText: "...como prioridad invertiremos $20,000,000 para construir 50 escuelas equipadas en los primeros 4 años...",
      highlightedText: "construir 50 escuelas equipadas",
      highlightClass: "bg-gray-700 text-white",
      page: "18", metaReq: "12.5", metaHist: "12.5",
      calcMsg: "La meta requerida representa <strong class='font-medium text-white'>1× el promedio histórico registrado</strong>, manteniéndose en línea con la ejecución anterior.",
      barWidth: "16%", mult: "1×", isAlert: false
    };

    setDrawerData(data);
    setIsDrawerOpen(true);
  };

  const handleFollowUp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    const current = prompt;
    setPrompt('');
    setChatHistory(prev => [...prev, { type: 'user', text: current }, { type: 'loader' }]);
    
    setTimeout(() => {
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist.pop();
        return [...newHist, { type: 'ai' }];
      });
    }, 2000);
  };

  return (
    <motion.main 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8 }}
      className="min-h-screen bg-dark text-white pt-32 pb-32 px-6 relative z-10"
    >
      <div className="max-w-5xl mx-auto mb-12">
        <button 
          onClick={() => router.back()} 
          className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.3em] text-gray-500 hover:text-white transition-colors w-max"
        >
          <ArrowLeft className="w-3 h-3" /> Volver
        </button>
      </div>

      <div className="max-w-5xl mx-auto flex flex-col gap-16">
        {chatHistory.map((msg, i) => {
          if (msg.type === 'user') {
            return (
              <div key={i} className="flex justify-end opacity-0 transform translate-y-8 chat-msg">
                <div className="border border-white/5 bg-white/5 backdrop-blur-md px-8 py-6 rounded-2xl max-w-3xl">
                  <p className="text-white font-light text-lg whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                </div>
              </div>
            );
          }
          if (msg.type === 'loader') {
            return (
              <div key={i} className="flex justify-start opacity-0 chat-msg">
                <div className="flex gap-4 items-center py-4">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:0.2s]"></div>
                    <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:0.4s]"></div>
                  </div>
                  <span className="text-[10px] font-mono tracking-[0.3em] text-gray-500 uppercase">Procesando Evidencia...</span>
                </div>
              </div>
            );
          }
          if (msg.type === 'ai') {
            return (
              <div key={i} className="flex flex-col gap-10 opacity-0 transform translate-y-8 chat-msg w-full">
                <div className="pl-6 border-l border-accent">
                  <div className="flex items-center gap-3 mb-4 text-[10px] font-mono text-accent uppercase tracking-[0.3em]">
                    <Search className="w-3 h-3" /> Síntesis de Evidencia
                  </div>
                  <p className="text-gray-300 font-light leading-relaxed text-xl max-w-4xl font-playfair">
                    Se encontraron compromisos oficiales en los planes de gobierno. El <span className="text-white font-normal">Candidato A</span> propone construir 300 unidades educativas sin especificar presupuesto en su plan. El <span className="text-white font-normal">Candidato B</span> propone 50 escuelas con un presupuesto asignado de $20 millones. A continuación, el desglose de datos extraídos.
                  </p>
                </div>
                <div className="grid md:grid-cols-2 gap-8 w-full">
                  <EvidenceCard
                    id="EVIDENCIA-01" candidateName="Candidato A" title="300 Unidades Educativas" action="Construir" deadline="4 años" budget="No especificado" accentColorClass="bg-accent" onAuditClick={() => openDrawer('A01')}
                  />
                  <EvidenceCard
                    id="EVIDENCIA-02" candidateName="Candidato B" title="50 Escuelas Equipadas" action="Construir y equipar" deadline="4 años" budget="$20,000,000" accentColorClass="bg-gray-500" onAuditClick={() => openDrawer('B01')}
                  />
                </div>
              </div>
            );
          }
          return null;
        })}

        <div ref={chatBottomRef} />
      </div>

      {/* Chat Input for Follow-ups */}
      <div className="fixed bottom-0 left-0 right-0 p-8 bg-gradient-to-t from-dark via-dark/95 to-transparent backdrop-blur-sm">
        <form onSubmit={handleFollowUp} className="max-w-5xl mx-auto relative group">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Haz una pregunta de seguimiento..."
            className="w-full bg-surface/50 border border-white/5 hover:border-white/20 focus:border-accent/50 text-white px-8 py-5 rounded-full focus:outline-none font-light placeholder-gray-500 transition-colors shadow-2xl"
          />
          <button type="submit" disabled={!prompt.trim()} className="absolute right-3 top-1/2 -translate-y-1/2 bg-white text-dark p-3 rounded-full hover:bg-gray-200 transition-colors disabled:opacity-30">
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>

      <AuditDrawer 
        isOpen={isDrawerOpen} 
        onClose={() => setIsDrawerOpen(false)}
        evidenceData={drawerData}
      />
    </motion.main>
  );
}
