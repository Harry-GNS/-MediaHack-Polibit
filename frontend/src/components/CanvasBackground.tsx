"use client";

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function CanvasBackground() {
  const groupRef = useRef<THREE.Group>(null);
  
  // Usaremos un Icosaedro para tener una distribución uniforme de puntos y red
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(2.5, 4), []); // detail 4 = ~2562 vertices
  
  // Guardamos las posiciones originales para calcular el ruido sin perder la forma base
  const originalPositions = useMemo(() => {
    return new Float32Array(geometry.attributes.position.array);
  }, [geometry]);

  useFrame((state) => {
    if (!groupRef.current) return;
    const time = state.clock.getElapsedTime();
    
    // Interacción suave con el mouse (Lerp)
    const targetX = (state.pointer.x * Math.PI) * 0.1;
    const targetY = (state.pointer.y * Math.PI) * 0.1;
    
    groupRef.current.rotation.y += 0.002; // Rotación constante
    groupRef.current.rotation.x += 0.001;
    
    // Inclinación por cursor
    groupRef.current.rotation.y += 0.05 * (targetX - groupRef.current.rotation.y);
    groupRef.current.rotation.x += 0.05 * (-targetY - groupRef.current.rotation.x);

    // Animación orgánica "Respiración" y deformación por ruido (Noise)
    const positions = geometry.attributes.position.array as Float32Array;
    
    for (let i = 0; i < positions.length; i += 3) {
      const ox = originalPositions[i];
      const oy = originalPositions[i + 1];
      const oz = originalPositions[i + 2];
      
      const length = Math.sqrt(ox*ox + oy*oy + oz*oz);
      const nx = ox / length;
      const ny = oy / length;
      const nz = oz / length;
      
      // Combinación de senos y cosenos espaciales para simular Perlin Noise
      const noise = Math.sin(ox * 1.5 + time) * Math.cos(oy * 1.5 + time * 0.8) * Math.sin(oz * 1.5 + time * 1.2);
      const wave = noise * 0.15; // Intensidad de la deformación
      
      positions[i] = ox + nx * wave;
      positions[i + 1] = oy + ny * wave;
      positions[i + 2] = oz + nz * wave;
    }
    
    geometry.attributes.position.needsUpdate = true;
  });

  return (
    <>
      <fog attach="fog" args={['#050508', 3, 8]} />
      <group ref={groupRef}>
        {/* La red (Plexus/Líneas) */}
        <mesh geometry={geometry}>
          <meshBasicMaterial 
            color="#0066ff" 
            wireframe={true} 
            transparent={true} 
            opacity={0.08} 
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
        
        {/* Los Nodos (Puntos brillantes) */}
        <points geometry={geometry}>
          <pointsMaterial
            size={0.025}
            color="#00d2ff"
            transparent={true}
            opacity={0.6}
            blending={THREE.AdditiveBlending}
            sizeAttenuation={true}
            depthWrite={false}
          />
        </points>

        {/* Halo interno para el núcleo */}
        <mesh>
          <sphereGeometry args={[2.2, 32, 32]} />
          <meshBasicMaterial 
            color="#b026ff" 
            transparent={true} 
            opacity={0.03} 
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      </group>
    </>
  );
}
