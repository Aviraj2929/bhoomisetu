// Backend address. On Vercel set VITE_API_URL (no trailing slash). Locally it falls back to localhost.
const ROOT = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';
export const API_BASE = `${ROOT.replace(/\/$/, '')}/api/v1`;
