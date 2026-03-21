const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function resolveConnectSources() {
  const sources = new Set(["'self'"]);

  if (/^https?:\/\//.test(apiBaseUrl)) {
    try {
      sources.add(new URL(apiBaseUrl).origin);
    } catch {
      // Ignore malformed env values and keep the default self origin only.
    }
  }

  return Array.from(sources).join(" ");
}

const contentSecurityPolicy = [
  "default-src 'self'",
  `connect-src ${resolveConnectSources()}`,
  "img-src 'self' data: blob:",
  "style-src 'self' 'unsafe-inline'",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  "font-src 'self' data:",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: contentSecurityPolicy },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
