import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.uploadthing.com",
      },
    ],
  },
  // Fix for SSE - disable response buffering
  async headers() {
    return [
      {
        source: "/api/v1/scan/:path*",
        headers: [
          {
            key: "Transfer-Encoding",
            value: "chunked",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
