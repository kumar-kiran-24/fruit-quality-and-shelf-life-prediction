import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { API_CONFIG } from '../config/api.config'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function safeNumber(value: any, fallback: number = 0): number {
  if (value === null || value === undefined) return fallback
  const num = typeof value === 'number' ? value : parseFloat(value)
  return isNaN(num) ? fallback : num
}

export function safeFixed(value: any, decimals: number = 1, fallback: string = 'N/A'): string {
  if (value === null || value === undefined) return fallback
  const num = typeof value === 'number' ? value : parseFloat(value)
  if (isNaN(num)) return fallback
  return num.toFixed(decimals)
}

export function getImageUrl(img: any): string | null {
  if (!img) return null
  const path = typeof img === 'string' ? img : (img.url || img.image_path || img.path || img.src)
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path
  }
  const apiBase = API_CONFIG.BASE_URL.replace(/\/api\/v1\/?$/, '')
  return `${apiBase}${path.startsWith('/') ? '' : '/'}${path}`
}

