import { API_CONFIG } from '../config/api.config'

export function getAuthHeaders(): HeadersInit {
  if (typeof window === 'undefined') return {}
  const token = localStorage.getItem('orchard_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  }

  // If body is FormData, don't set Content-Type so browser sets boundary automatically
  if (!(options.body instanceof FormData) && !Object.keys(headers).some(h => h.toLowerCase() === 'content-type')) {
    (headers as any)['Content-Type'] = 'application/json'
  }

  const url = `${API_CONFIG.BASE_URL}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`
    try {
      const data = await response.json()
      errorMessage = data.detail || data.message || errorMessage
    } catch (_) {}
    throw new Error(errorMessage)
  }

  return response.json() as Promise<T>
}
