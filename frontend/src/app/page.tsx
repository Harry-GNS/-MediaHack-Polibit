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
      <div className="absolute inset-0 z-0 pointer-events-none bg-[#020202] overflow-hidden">
        {/* Grain overlay for noise texture */}
        <div 
          className="absolute inset-0 z-20 opacity-40 mix-blend-overlay pointer-events-none" 
          style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22/%3E%3C/svg%3E")' }}
        ></div>

        <Canvas>
          <CanvasBackground />
        </Canvas>
      </div>

      {/* VIEW 1: INTRO */}
      <div ref={introRef} className="absolute inset-0 flex flex-col items-center justify-center z-20">

        {/* Contenedor Central */}
        <div className="relative w-full flex items-center justify-center h-full z-10 px-4 pointer-events-none -translate-y-6 md:-translate-y-10 lg:-translate-y-12">
          
          {/* Texto Izquierdo (Desplazado hacia arriba) */}
          <div className="absolute right-[50%] mr-2 md:mr-3 mb-10 md:mb-16 lg:mb-20 z-10 intro-item transform translate-y-8 opacity-0 flex items-center justify-end">
            <h1 className="text-7xl md:text-[110px] lg:text-[150px] xl:text-[180px] font-light tracking-tighter text-white leading-none">
              Condor
            </h1>
          </div>

          {/* Texto Derecho (Desplazado hacia abajo) */}
          <div className="absolute left-[50%] ml-2 md:ml-3 mt-10 md:mt-16 lg:mt-20 z-10 intro-item transform translate-y-8 opacity-0 flex items-center justify-start">
            <h1 className="text-7xl md:text-[110px] lg:text-[150px] xl:text-[180px] font-black text-accent drop-shadow-[0_0_20px_rgba(0,210,255,0.4)] tracking-tighter leading-none">
              Lens
            </h1>
          </div>

          {/* Slogan */}
          <div className="absolute top-[62%] md:top-[68%] w-full flex justify-center z-10 intro-item transform translate-y-8 opacity-0 px-4">
            <p className="text-[10px] md:text-xs text-gray-400 font-light max-w-3xl text-center leading-relaxed tracking-[0.15em] uppercase">
              Visión panorámica sobre el poder.<br />Escrutinio algorítmico y evidencia en alta resolución.
            </p>
          </div>
        </div>

        {/* Botones Inferiores Centrados */}
        <div className="absolute bottom-16 z-30 intro-item transform translate-y-8 opacity-0 w-full px-4 flex flex-col md:flex-row justify-center gap-6 md:gap-16 lg:gap-24 items-center">
          <button onClick={() => handleNav('/verify')} className="px-10 py-4 bg-white text-dark rounded-full font-bold hover:bg-gray-200 transition-all flex items-center justify-center gap-3 shadow-[0_0_30px_rgba(255,255,255,0.15)] uppercase tracking-widest text-xs hover:scale-105 duration-300 min-w-[240px]">
            Iniciar Auditoría
          </button>

          <button onClick={() => handleNav('/comparacion')} className="px-10 py-4 bg-black/40 border border-white/20 text-white rounded-full font-medium hover:bg-white/10 transition-all flex items-center justify-center gap-3 uppercase tracking-widest text-xs hover:scale-105 duration-300 backdrop-blur-md min-w-[240px]">
            Comparar planes
          </button>
        </div>
      </div>
    </motion.main>
  );
}
