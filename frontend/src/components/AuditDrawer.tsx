"use client";

import { useEffect, useRef } from "react";
import { X, ExternalLink } from "lucide-react";
import gsap from "gsap";

interface AuditData {
  id: string;
  sourceText: string;
  highlightedText: string;
  highlightClass?: string;
  page: string;
  metaReq: string;
  metaHist: string;
  calcMsg: string;
  barWidth: string; // e.g. "100%", "16%"
  mult: string; // e.g. "6×", "1×"
  isAlert: boolean;
}

interface AuditDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  data: AuditData | null;
}

export default function AuditDrawer({ isOpen, onClose, data }: AuditDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      gsap.to(overlayRef.current, { opacity: 1, duration: 0.3, display: "block" });
      gsap.to(drawerRef.current, { x: 0, duration: 0.6, ease: "expo.out" });
      
      if (barRef.current && data) {
        gsap.fromTo(
          barRef.current, 
          { width: "0%" }, 
          { width: data.barWidth, duration: 1.5, ease: "power3.out", delay: 0.3 }
        );
      }
    } else {
      gsap.to(drawerRef.current, { x: "100%", duration: 0.5, ease: "power3.inOut" });
      gsap.to(overlayRef.current, { 
        opacity: 0, 
        duration: 0.3, 
        onComplete: () => {
          if (overlayRef.current) overlayRef.current.style.display = "none";
        }
      });
    }
  }, [isOpen, data]);

  return (
    <>
      <div 
        ref={overlayRef} 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 hidden opacity-0" 
        onClick={onClose}
      />
      
      <aside 
        ref={drawerRef}
        className="fixed top-0 right-0 w-full max-w-md h-full bg-[#0a0a0c] border-l border-border z-50 flex flex-col shadow-2xl translate-x-full text-white text-left"
      >
        <div className="p-6 border-b border-border flex justify-between items-center bg-surface">
          <div>
            <h4 className="text-[10px] font-mono text-accent tracking-widest uppercase flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse"></span>
              Auditoría de Datos
            </h4>
            <div className="text-xs text-white font-mono mt-2">
              ID: <span className="text-gray-500">EV-2026-{data?.id || '---'}</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-surface border border-transparent hover:border-border transition-colors">
            <X className="w-5 h-5 text-gray-400 hover:text-white" />
          </button>
        </div>

        <div className="p-6 flex-grow overflow-y-auto">
          {data && (
            <>
              {/* Fuente Primaria */}
              <div className="mb-10">
                <h5 className="font-mono text-[10px] text-gray-500 uppercase tracking-widest mb-3">A. Fuente Primaria</h5>
                <div className="p-5 bg-grid border border-border relative">
                  <p className="font-serif italic text-gray-300 leading-relaxed text-sm">
                    {data.sourceText.split(data.highlightedText)[0]}
                    <span className={`px-1 ${data.highlightClass || "bg-accentMuted text-accent"}`}>
                      {data.highlightedText}
                    </span>
                    {data.sourceText.split(data.highlightedText)[1]}
                  </p>
                  <div className="mt-4 pt-3 border-t border-border/50 flex justify-between items-center text-[10px] font-mono">
                    <span className="text-gray-400">Plan de Gobierno Oficial</span>
                    <a href="#" className="text-accent hover:underline flex items-center gap-1">Pág. {data.page} <ExternalLink className="w-3 h-3"/></a>
                  </div>
                </div>
              </div>

              {/* Contexto Oficial */}
              <div className="mb-10">
                <h5 className="font-mono text-[10px] text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                  B. Contexto Oficial (SERCOP / INEC)
                </h5>
                <div className="grid grid-cols-2 gap-4 font-mono">
                  <div className="p-4 bg-surface border border-border">
                    <div className="text-gray-500 text-[10px] uppercase tracking-wider mb-2">Meta Requerida</div>
                    <div className="text-3xl text-white font-light">{data.metaReq}<span className="text-xs text-gray-500 ml-1">/año</span></div>
                  </div>
                  <div className="p-4 bg-surface border border-border">
                    <div className="text-gray-500 text-[10px] uppercase tracking-wider mb-2">Prom. Histórico</div>
                    <div className="text-3xl text-white font-light">{data.metaHist}<span className="text-xs text-gray-500 ml-1">/año</span></div>
                  </div>
                </div>
              </div>

              {/* Cálculo Objetivo */}
              <div className="p-6 border border-accent/30 bg-accent/5 tech-corners">
                <div className="corner-bottom"></div>
                <div className="font-mono text-[10px] tracking-widest text-accent mb-3 uppercase">C. Cálculo Objetivo</div>
                <p className="text-sm font-light mb-6 text-gray-300 leading-relaxed" dangerouslySetInnerHTML={{ __html: data.calcMsg }} />
                
                <div className="relative h-1.5 w-full bg-surface border border-border rounded-full overflow-hidden flex">
                  <div className="h-full bg-gray-500 w-[16%] z-10 border-r border-dark"></div>
                  <div ref={barRef} className={`h-full z-0 opacity-80 ${data.isAlert ? 'bg-accent' : 'bg-gray-400'}`} style={{ width: '0%' }}></div>
                </div>
                <div className="flex justify-between text-[10px] font-mono text-gray-500 mt-3">
                  <span>Base (1×)</span>
                  <span className={data.isAlert ? 'text-accent' : 'text-gray-400'}>Requerido ({data.mult})</span>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="p-6 border-t border-border grid grid-cols-2 gap-4 bg-[#0a0a0c]">
          <button className="py-3 border border-border text-xs font-mono uppercase tracking-wider hover:bg-surface transition-colors flex justify-center items-center gap-2 text-white">
            Copiar Enlace
          </button>
          <button className="py-3 bg-white text-dark text-xs font-mono uppercase tracking-wider hover:bg-gray-200 transition-colors flex justify-center items-center gap-2">
            Exportar CSV
          </button>
        </div>
      </aside>
    </>
  );
}
