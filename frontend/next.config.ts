import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Next 16 ya no admite las opciones individuales de devIndicators.
  devIndicators: false,
  async rewrites() {
    const backend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/backend/:path*", destination: `${backend}/:path*` }];
  },
};

export default nextConfig;
