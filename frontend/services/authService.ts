import { apiRequest } from '../lib/apiClient'
import { API_CONFIG } from '../config/api.config'

export interface UserRegisterPayload {
  name: string
  email: string
  password: string
  address?: string
  city?: string
  state?: string
  country?: string
  pincode?: string
  phone_number?: string
}

export interface UserLoginPayload {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  name: string
  email: string
  role: string
}

export interface UserResponse {
  id: number
  user_id: string
  name: string
  email: string
  address?: string | null
  city?: string | null
  state?: string | null
  country?: string | null
  pincode?: string | null
  phone_number?: string | null
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const TOKEN_KEY = 'orchard_token'
const USER_KEY = 'orchard_user'

export const authService = {
  async registerUser(payload: UserRegisterPayload): Promise<UserResponse> {
    return apiRequest<UserResponse>(API_CONFIG.ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  async loginUser(payload: UserLoginPayload): Promise<TokenResponse> {
    const data = await apiRequest<TokenResponse>(API_CONFIG.ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    if (data.access_token) {
      this.setAuthSession(data.access_token, {
        id: data.user_id,
        name: data.name,
        email: data.email,
        role: data.role,
      })
    }

    return data
  },

  async getCurrentUser(): Promise<UserResponse> {
    const user = await apiRequest<UserResponse>(API_CONFIG.ENDPOINTS.ME)
    if (user) {
      const storedUser = {
        id: user.user_id,
        name: user.name,
        email: user.email,
        role: user.role,
        address: user.address,
      }
      if (typeof window !== 'undefined') {
        localStorage.setItem(USER_KEY, JSON.stringify(storedUser))
      }
    }
    return user
  },

  logoutUser(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  },

  getStoredToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(TOKEN_KEY)
  },

  getStoredUser(): { id?: string; name?: string; email?: string; role?: string; address?: string } | null {
    if (typeof window === 'undefined') return null
    const userStr = localStorage.getItem(USER_KEY)
    if (!userStr) return null
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  },

  setAuthSession(token: string, user: { id: string; name: string; email: string; role: string }): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    }
  },
}
