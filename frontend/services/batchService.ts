export interface Batch {
  id: string
  name: string
  date: string
  images: number
  apples: number
  shelf: string
  status: string
  buyer: string
  score: number
  notes?: string
}

const DEFAULT_BATCHES: Batch[] = [
  { id: 'OB-2407-018', name: 'Honeycrisp · North Block', date: 'Jul 18, 2024', images: 12, apples: 428, shelf: '18 days', status: 'Ready for dispatch', buyer: 'FreshFields Market', score: 94 },
  { id: 'OB-2407-017', name: 'Gala · East Orchard', date: 'Jul 17, 2024', images: 8, apples: 301, shelf: '12 days', status: 'Detection complete', buyer: '—', score: 87 },
  { id: 'OB-2407-016', name: 'Pink Lady · Ridge 4', date: 'Jul 15, 2024', images: 16, apples: 612, shelf: '24 days', status: 'Buyer recommended', buyer: 'Harvest & Co.', score: 96 },
  { id: 'OB-2407-015', name: 'Granny Smith · South', date: 'Jul 12, 2024', images: 6, apples: 198, shelf: '9 days', status: 'Dispatched', buyer: 'Green Basket', score: 79 },
]

function getStorage(): Batch[] {
  if (typeof window === 'undefined') return DEFAULT_BATCHES
  const stored = localStorage.getItem('orchard_batches')
  if (!stored) {
    localStorage.setItem('orchard_batches', JSON.stringify(DEFAULT_BATCHES))
    return DEFAULT_BATCHES
  }
  try {
    return JSON.parse(stored) as Batch[]
  } catch (e) {
    return DEFAULT_BATCHES
  }
}

function setStorage(batches: Batch[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('orchard_batches', JSON.stringify(batches))
  }
}

export const batchService = {
  getBatches(): Batch[] {
    return getStorage()
  },
  
  getBatchById(id: string): Batch | undefined {
    return getStorage().find(b => b.id === id)
  },
  
  createBatch(batchData: { name: string; block: string; date: string; notes: string; imageCount: number }): Batch {
    const batches = getStorage()
    // Generate sequential style ID
    const yearMonth = new Date(batchData.date).toISOString().slice(2, 7).replace('-', '') // e.g. "2408"
    const nextSeq = String(batches.length + 15).padStart(3, '0')
    const id = `OB-${yearMonth}-${nextSeq}`
    
    // Simulate smart quality detection metrics
    const apples = batchData.imageCount * Math.floor(Math.random() * 20 + 25)
    const score = Math.floor(Math.random() * 25 + 75)
    const shelfDays = Math.floor(Math.random() * 15 + 8)
    
    const newBatch: Batch = {
      id,
      name: `${batchData.name} · ${batchData.block}`,
      date: new Date(batchData.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      images: batchData.imageCount,
      apples,
      shelf: `${shelfDays} days`,
      status: 'Detection complete',
      buyer: '—',
      score,
      notes: batchData.notes
    }
    
    batches.unshift(newBatch)
    setStorage(batches)
    return newBatch
  },
  
  updateBatch(id: string, updates: Partial<Batch>): Batch | undefined {
    const batches = getStorage()
    const idx = batches.findIndex(b => b.id === id)
    if (idx === -1) return undefined
    const updated = { ...batches[idx], ...updates }
    batches[idx] = updated
    setStorage(batches)
    return updated
  },
  
  getStats() {
    const batches = getStorage()
    const active = batches.filter(b => b.status !== 'Dispatched').length
    const apples = batches.reduce((sum, b) => sum + b.apples, 0)
    const ready = batches.filter(b => b.status === 'Ready for dispatch').length
    return {
      total: batches.length,
      active,
      apples,
      ready
    }
  }
}
