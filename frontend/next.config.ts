import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vivaldi/Chrome pueden abrir el proyecto como 127.0.0.1 mientras Next se
  // inicia en localhost. Sin este origen, Next bloquea los recursos de
  // desarrollo (403) y React no hidrata los botones del formulario.
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
