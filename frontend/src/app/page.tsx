"use client";

import { useState, useRef, useEffect } from 'react';
import { Search, ArrowRight, Play } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@react-three/fiber'; // if we want to use hook, but standard gsap is fine
import { Canvas } from '@react-three/fiber';

// Components
import CanvasBackground from '@/components/CanvasBackground';
import EvidenceCard from '@/components/EvidenceCard';
import AuditDrawer from '@/components/AuditDrawer';

type AppState = 'INTRO' | 'SEARCH' | 'CHAT';

export default function Home() {
  const [currentState, setCurrentState] = useState<AppState>('INTRO');
  const [prompt, setPrompt] = useState('');
  const [chatHistory, setChatHistory] = useState<{type: 'user' | 'loader' | 'ai', text?: string}[]>([]);
  const [drawerData, setDrawerData] = useState<any>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Refs for animations
  const introRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initial Intro Animation
  useEffect(() => {
    if (currentState === 'INTRO') {
      gsap.to('.intro-item', {
        y: 0, opacity: 1, duration: 1, stagger: 0.2, ease: "power3.out", delay: 0.2
      });
    }
  }, []);

  const handleStart = () => {
    gsap.to(introRef.current, {
      opacity: 0, y: -20, duration: 0.5, pointerEvents: "none",
      onComplete: () => {
        setCurrentState('SEARCH');
        gsap.to(searchRef.current, {
          opacity: 1, duration: 0.8, pointerEvents: "auto", ease: "power2.out"
        });
      }
    });
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim()) return;

    const currentPrompt = prompt;
    setPrompt('');

    if (currentState === 'SEARCH') {
      // Transition from SEARCH to CHAT
      const tl = gsap.timeline();
      tl.to('.search-extras', {
        opacity: 0, height: 0, margin: 0, duration: 0.3, overflow: "hidden"
      })
      .to(searchContainerRef.current, {
        top: "auto", bottom: "1.5rem", translateY: 0, duration: 0.8, ease: "power3.inOut"
      }, "-=0.2");

      gsap.to(chatRef.current, { opacity: 1, pointerEvents: "auto", duration: 0.5, delay: 0.5 });
      setCurrentState('CHAT');
    }

    // Add user message
    setChatHistory(prev => [...prev, { type: 'user', text: currentPrompt }, { type: 'loader' }]);
    
    // Simulate AI response
    setTimeout(() => {
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist.pop(); // remove loader
        return [...newHist, { type: 'ai' }];
      });
    }, 2000);
  };

  // Auto-scroll chat
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    // Animate new chat messages
    gsap.to('.chat-msg:not(.animated)', {
      opacity: 1, y: 0, duration: 0.5, stagger: 0.1,
      onComplete: function() {
        this.targets().forEach(el => el.classList.add('animated'));
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

  return (
    <main className="min-h-screen relative font-sans text-white">
      {/* 1. BACKGROUND */}
      <div className="fixed inset-0 z-[-1] pointer-events-none">
        <Canvas>
          <CanvasBackground />
        </Canvas>
      </div>

      {/* VIEW 1: INTRO */}
      <div ref={introRef} className={`absolute inset-0 flex flex-col items-center justify-center z-20 ${currentState !== 'INTRO' ? 'pointer-events-none opacity-0' : ''}`}>
        <div className="intro-item transform translate-y-4 opacity-0 inline-flex items-center gap-2 border border-border bg-surface px-3 py-1 rounded-full text-[10px] font-mono text-accent mb-6 tracking-widest uppercase">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
          Plataforma Neutral de Datos
        </div>
        
        <h1 className="intro-item transform translate-y-4 opacity-0 text-5xl md:text-7xl font-light tracking-tight mb-8">
          Evidencia <span className="font-semibold">Electoral</span>
        </h1>
        
        <button onClick={handleStart} className="intro-item transform translate-y-4 opacity-0 px-8 py-3 bg-white text-dark rounded font-medium hover:bg-gray-200 transition-colors flex items-center gap-2">
          Iniciar Auditoría
          <Play className="w-4 h-4" />
        </button>
      </div>

      {/* VIEW 2/3: GLOBAL SEARCH BAR */}
      <div 
        ref={searchContainerRef}
        id="global-search" 
        className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-3xl px-6 z-30 ${currentState === 'INTRO' ? 'opacity-0 pointer-events-none' : ''}`}
      >
        <div className="search-extras text-center mb-8">
          <h2 className="text-3xl font-light">¿Qué promesas quieres verificar hoy?</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="relative glass rounded-lg flex items-center p-2 shadow-2xl transition-all">
          <div className="absolute -inset-1 bg-gradient-to-r from-accent to-blue-800 rounded-lg blur opacity-20 transition duration-700"></div>
          <div className="relative w-full flex items-center bg-dark/50 rounded z-10">
            <Search className="w-5 h-5 text-gray-400 ml-4" />
            <input 
              type="text" 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ej: Compara las propuestas de educación..." 
              className="w-full bg-transparent border-none text-white px-4 py-4 focus:outline-none font-light placeholder-gray-500"
            />
            <button type="submit" className="bg-white text-dark px-6 py-2 rounded font-medium hover:bg-gray-200 transition-colors text-sm mr-2 whitespace-nowrap">
              Enviar
            </button>
          </div>
        </form>
        
        {/* Chips */}
        <div className="search-extras flex flex-wrap justify-center gap-3 mt-6">
          <span onClick={() => setPrompt('¿Qué proponen sobre la construcción de nuevas escuelas?')} className="px-3 py-1.5 text-xs font-mono border border-border bg-surface rounded text-gray-400 hover:text-accent hover:border-accent cursor-pointer transition-all">/educacion</span>
          <span onClick={() => setPrompt('Compara el presupuesto para seguridad')} className="px-3 py-1.5 text-xs font-mono border border-border bg-surface rounded text-gray-400 hover:text-accent hover:border-accent cursor-pointer transition-all">/seguridad_presupuesto</span>
        </div>
      </div>

      {/* VIEW 3: RESULTS (CHAT HISTORY) */}
      <div ref={chatRef} className={`absolute inset-0 z-10 pt-8 pb-32 px-6 overflow-y-auto ${currentState !== 'CHAT' ? 'opacity-0 pointer-events-none' : ''}`}>
        <div className="max-w-4xl mx-auto flex flex-col gap-10">
          
          {chatHistory.map((msg, i) => {
            if (msg.type === 'user') {
              return (
                <div key={i} className="flex justify-end opacity-0 transform translate-y-4 chat-msg">
                  <div className="glass px-6 py-4 rounded-t-xl rounded-bl-xl max-w-2xl border-accent/20">
                    <p className="text-white font-light">{msg.text}</p>
                  </div>
                </div>
              );
            }
            if (msg.type === 'loader') {
              return (
                <div key={i} className="flex justify-start opacity-0 chat-msg">
                  <div className="flex gap-2 items-center text-accent py-4">
                    <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
                    <div className="w-2 h-2 bg-accent rounded-full typing-dot"></div>
                    <span className="ml-2 text-xs font-mono tracking-widest text-gray-500 uppercase">Consultando evidencia...</span>
                  </div>
                </div>
              );
            }
            if (msg.type === 'ai') {
              return (
                <div key={i} className="flex flex-col gap-6 opacity-0 transform translate-y-4 chat-msg max-w-4xl w-full">
                  <div className="pl-4 border-l-2 border-accent">
                    <div className="flex items-center gap-2 mb-2 text-xs font-mono text-gray-500 uppercase tracking-wider">
                      <Search className="w-4 h-4" /> Síntesis de Evidencia
                    </div>
                    <p className="text-gray-300 font-light leading-relaxed text-lg">
                      Se encontraron compromisos oficiales en los planes de gobierno. El <span className="text-white font-medium">Candidato A</span> propone construir 300 unidades educativas sin especificar presupuesto en su plan. El <span className="text-white font-medium">Candidato B</span> propone 50 escuelas con un presupuesto asignado de $20 millones. A continuación, el desglose de datos extraídos.
                    </p>
                  </div>
                  <div className="grid md:grid-cols-2 gap-6 w-full">
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
      </div>

      <AuditDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} data={drawerData} />
    </main>
  );
}
