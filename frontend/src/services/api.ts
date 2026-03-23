// Em dev: Vite proxy /api → backend:8000
// Em prod: frontend servido pelo backend, chamadas diretas
const API_BASE = import.meta.env.DEV ? "/api" : ""

export async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  return response.json() as Promise<T>
}
