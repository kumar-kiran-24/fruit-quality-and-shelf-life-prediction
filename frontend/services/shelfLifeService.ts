import { batchService } from './batchService'

export const shelfLifeService = {
  getAverageShelfLife(): number {
    const batches = batchService.getBatches().filter(b => b.status !== 'Dispatched')
    if (batches.length === 0) return 0
    const totalDays = batches.reduce((sum, b) => {
      const days = parseInt(b.shelf.split(' ')[0]) || 0
      return sum + days
    }, 0)
    return parseFloat((totalDays / batches.length).toFixed(1))
  },
  
  getAverageQuality(): number {
    const batches = batchService.getBatches().filter(b => b.status !== 'Dispatched')
    if (batches.length === 0) return 0
    const totalScore = batches.reduce((sum, b) => sum + b.score, 0)
    return Math.round(totalScore / batches.length)
  }
}
