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
  const authHeaders = getAuthHeaders()
  const headers: Record<string, string> = {
    ...(authHeaders as Record<string, string>),
    ...(options.headers as Record<string, string>),
  }

  const method = (options.method || 'GET').toUpperCase()
  // Only set Content-Type for requests with a body that is not FormData
  const hasBody = options.body !== undefined && method !== 'GET' && method !== 'HEAD'
  if (hasBody && !(options.body instanceof FormData) && !Object.keys(headers).some(h => h.toLowerCase() === 'content-type')) {
    headers['Content-Type'] = 'application/json'
  }

  const url = `${API_CONFIG.BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      // Clear session if token is invalid or expired
      if (response.status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem('orchard_token')
        localStorage.removeItem('orchard_user')
      }

      let errorMessage = `HTTP Error ${response.status}`
      try {
        const data = await response.json()
        if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (Array.isArray(data.detail)) {
          errorMessage = data.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(', ')
        } else if (data.message) {
          errorMessage = data.message
        }
      } catch (_) {}
      throw new Error(errorMessage)
    }

    return response.json() as Promise<T>
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      throw new Error(`Unable to connect to backend server at ${API_CONFIG.BASE_URL}. Please verify your backend server is running and accessible.`)
    }
    throw err
  }
}
