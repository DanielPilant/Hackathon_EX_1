const trimTrailingSlash = (value) => value.replace(/\/+$/, "");

const apiBase = trimTrailingSlash(
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
);

const wsBase = trimTrailingSlash(
  import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000"
);

const framesWsBase = trimTrailingSlash(
  import.meta.env.VITE_FRAMES_WS_BASE_URL || "ws://localhost:8000"
);

export const API_BASE_URL = apiBase;
export const WS_BASE_URL = wsBase;
export const FRAMES_WS_BASE_URL = framesWsBase;

export const buildWsCandidates = (path) => {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const candidates = [
    `${WS_BASE_URL}${normalizedPath}`,
    `${FRAMES_WS_BASE_URL}${normalizedPath}`,
    `ws://localhost:8000${normalizedPath}`,
    `ws://127.0.0.1:8000${normalizedPath}`,
  ];

  return [...new Set(candidates)];
};