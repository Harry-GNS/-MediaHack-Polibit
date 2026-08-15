"use client";

import { useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import gsap from 'gsap';
import { Canvas } from '@react-three/fiber';
import { motion } from 'framer-motion';

// Components
import CanvasBackground from '@/components/CanvasBackground';

export default function Home() {
  const router = useRouter();
  const introRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.to('.intro-item', {
      y: 0, opacity: 1, duration: 1.5, stagger: 0.2, ease: "power4.out", delay: 0.3
    });
  }, []);

  const handleNav = (path: string) => {
    if (!path) return;
    gsap.to(introRef.current, {
      opacity: 0, y: -40, duration: 0.6, ease: "power3.in",
      onComplete: () => {
        router.push(path);
      }
    });
  };

  return (
    <motion.main 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen relative"
    >
      {/* 1. BACKGROUND */}
      <div className="fixed inset-0 z-[-1] pointer-events-none">
        <Canvas>
          <CanvasBackground />
        </Canvas>
      </div>

      {/* VIEW 1: INTRO */}
      <div ref={introRef} className="absolute inset-0 flex flex-col items-center justify-center z-20">

        {/* Contenedor Central */}
        <div className="relative w-full max-w-7xl flex items-center justify-center h-full z-10 px-4">
          
          {/* Texto Izquierdo */}
          <div className="absolute left-4 md:left-12 lg:left-24 z-10 intro-item transform translate-y-8 opacity-0 flex flex-col items-start text-left">
            <h1 className="text-6xl md:text-8xl lg:text-[150px] font-light tracking-tight text-white leading-none">
              Condor
            </h1>
            <p className="mt-8 text-sm md:text-base text-gray-400 font-light max-w-xs md:max-w-sm leading-relaxed">
              Visión panorámica sobre el poder. Escrutinio algorítmico y evidencia en alta resolución.
            </p>
          </div>

          {/* Texto Derecho */}
          <div className="absolute right-4 md:right-12 lg:right-24 z-10 intro-item transform translate-y-8 opacity-0">
            <h1 className="text-6xl md:text-8xl lg:text-[150px] font-black text-accent drop-shadow-[0_0_15px_rgba(0,210,255,0.3)] leading-none">
              Lens
            </h1>
          </div>
        </div>

        {/* Botones Inferiores Centrados */}
        <div className="absolute bottom-16 z-30 intro-item transform translate-y-8 opacity-0 flex flex-col md:flex-row gap-4 md:gap-6 items-center">
          <button onClick={() => handleNav('/verify')} className="px-8 py-4 bg-white text-dark rounded-full font-bold hover:bg-gray-200 transition-all flex items-center gap-3 shadow-[0_0_30px_rgba(255,255,255,0.15)] uppercase tracking-widest text-xs hover:scale-105 duration-300">
            Iniciar Auditoría
          </button>

          <button onClick={() => handleNav('/comparacion')} className="px-8 py-4 bg-black/40 border border-white/20 text-white rounded-full font-medium hover:bg-white/10 transition-all flex items-center gap-3 uppercase tracking-widest text-xs hover:scale-105 duration-300 backdrop-blur-md">
            Comparar planes
          </button>

          <button className="px-8 py-4 bg-black/40 border border-white/10 text-white/50 rounded-full font-medium cursor-not-allowed transition-all flex items-center gap-3 uppercase tracking-widest text-xs backdrop-blur-md">
            Próximamente
          </button>
        </div>
      </div>
    </motion.main>
  );
}
