// Set VITE_API_URL in .env (see .env.example) or in the Vercel project settings.
// Falls back to the deployed Hugging Face Space.
const DEFAULT_API_URL = "";

export const API_BASE = (
  import.meta.env.VITE_API_URL || DEFAULT_API_URL
).replace(/\/+$/, "");
export const API_HOST = API_BASE.replace(/^https?:\/\//, "");

export const MAX_QUERY_CHARS = 2000;
export const REQUEST_TIMEOUT_MS = 90_000; // a sleeping Space can take a while to wake up
