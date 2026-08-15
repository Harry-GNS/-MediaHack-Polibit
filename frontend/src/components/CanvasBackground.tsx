"use client";

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function CanvasBackground() {
  const groupRef = useRef<THREE.Group>(null);
  
  // Capa Exterior
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(3.8, 4), []);
  const originalPositions = useMemo(() => new Float32Array(geometry.attributes.position.array), [geometry]);

  // Capa Interior (para rellenar el medio con nodos)
  const innerGeometry = useMemo(() => new THREE.IcosahedronGeometry(2.0, 3), []);
  const innerOriginalPositions = useMemo(() => new Float32Array(innerGeometry.attributes.position.array), [innerGeometry]);

  useFrame((state) => {
    if (!groupRef.current) return;
    const time = state.clock.getElapsedTime();
    
    // Interacción suave con el mouse (Lerp)
    const targetX = (state.pointer.x * Math.PI) * 0.1;
    const targetY = (state.pointer.y * Math.PI) * 0.1;
    
    groupRef.current.rotation.y += 0.002;
    groupRef.current.rotation.x += 0.001;
    
    // Inclinación por cursor
    groupRef.current.rotation.y += 0.05 * (targetX - groupRef.current.rotation.y);
    groupRef.current.rotation.x += 0.05 * (-targetY - groupRef.current.rotation.x);

    // Función para animar vértices
    const animateVertices = (geom: THREE.BufferGeometry, orig: Float32Array, waveScale: number) => {
      const positions = geom.attributes.position.array as Float32Array;
      for (let i = 0; i < positions.length; i += 3) {
        const ox = orig[i];
        const oy = orig[i + 1];
        const oz = orig[i + 2];
        
        const length = Math.sqrt(ox*ox + oy*oy + oz*oz);
        const nx = ox / length;
        const ny = oy / length;
        const nz = oz / length;
        
        const noise = Math.sin(ox * 1.5 + time) * Math.cos(oy * 1.5 + time * 0.8) * Math.sin(oz * 1.5 + time * 1.2);
        const wave = noise * waveScale;
        
        positions[i] = ox + nx * wave;
        positions[i + 1] = oy + ny * wave;
        positions[i + 2] = oz + nz * wave;
      }
      geom.attributes.position.needsUpdate = true;
    };

    animateVertices(geometry, originalPositions, 0.15);
    animateVertices(innerGeometry, innerOriginalPositions, 0.1);
  });

  return (
    <>
      <fog attach="fog" args={['#050508', 3, 8]} />
      <group ref={groupRef}>
        
        {/* --- CAPA EXTERIOR --- */}
        <mesh geometry={geometry}>
          <meshBasicMaterial 
            color="#0066ff" 
            wireframe={true} 
            transparent={true} 
            opacity={0.04} 
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
        <points geometry={geometry}>
          <pointsMaterial
            size={0.025}
            color="#00d2ff"
            transparent={true}
            opacity={0.3}
            blending={THREE.AdditiveBlending}
            sizeAttenuation={true}
            depthWrite={false}
          />
        </points>

        {/* --- CAPA INTERIOR (Nodos más tenues en el centro) --- */}
        <mesh geometry={innerGeometry}>
          <meshBasicMaterial 
            color="#0066ff" 
            wireframe={true} 
            transparent={true} 
            opacity={0.01} 
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </mesh>
        <points geometry={innerGeometry}>
          <pointsMaterial
            size={0.02}
            color="#00d2ff"
            transparent={true}
            opacity={0.1}
            blending={THREE.AdditiveBlending}
            sizeAttenuation={true}
            depthWrite={false}
          />
        </points>

        {/* Halo interno difuso para el núcleo */}
        <mesh>
          <sphereGeometry args={[3.0, 32, 32]} />
          <meshBasicMaterial 
            color="#b026ff" 
            transparent={true} 
            opacity={0.015} 
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      </group>
    </>
  );
}
