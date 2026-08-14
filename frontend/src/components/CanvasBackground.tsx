"use client";

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function CanvasBackground() {
  const pointsRef = useRef<THREE.Points>(null);

  // Generar las partículas
  const particleCount = 400;
  const positions = new Float32Array(particleCount * 3);
  for (let i = 0; i < particleCount * 3; i++) {
    positions[i] = (Math.random() - 0.5) * 10;
  }

  useFrame((state) => {
    if (!pointsRef.current) return;
    const time = state.clock.getElapsedTime();
    const mouseX = (state.pointer.x * window.innerWidth) / 2 * 0.0005;
    const mouseY = (state.pointer.y * window.innerHeight) / 2 * 0.0005;

    // Rotación base
    pointsRef.current.rotation.y += 0.001;
    pointsRef.current.rotation.x += 0.0005;

    // Interacción con mouse
    pointsRef.current.rotation.y += 0.05 * (mouseX - pointsRef.current.rotation.y);
    pointsRef.current.rotation.x += 0.05 * (-mouseY - pointsRef.current.rotation.x);
  });

  return (
    <>
      <fog attach="fog" args={['#08080a', 0.1, 8]} />
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.02}
          color="#00d2ff"
          transparent
          opacity={0.3}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </>
  );
}
