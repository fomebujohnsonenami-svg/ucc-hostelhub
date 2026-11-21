const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace(/\/+$/, '')

export function apiUrl(path: string) {
  return `${baseUrl}/${path.replace(/^\/+/, '')}`
}

function errorMessage(details: unknown): string | undefined {
  if (typeof details === 'string') return details
  if (Array.isArray(details)) return errorMessage(details[0])
  if (details && typeof details === 'object') return Object.values(details).map(errorMessage).find(Boolean)
}

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly details?: unknown) {
    super(errorMessage(details) ?? `API request failed with HTTP ${status}`)
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(apiUrl(path), { ...init, headers })
  if (!response.ok) throw new ApiError(response.status, await response.json().catch(() => undefined))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { signal })
}

export async function checkHealth(signal?: AbortSignal): Promise<void> {
  const health = await apiGet<{ status?: string } | null>('health/', signal)
  if (health?.status !== 'ok') throw new Error('Unexpected response from the API health endpoint')
}

export type ApiPage<T> = { count: number; next: string | null; previous: string | null; results: T[] }
export function payload(method: string, data?: unknown): RequestInit {
  return data === undefined ? { method } : { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }
}
