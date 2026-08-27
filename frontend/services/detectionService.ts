export interface DetectionResult {
  batchId: string
  totalDetected: number
  avgConfidence: string
  imagesAnalyzed: number
  imagesProcessed: string
  sparklineValues: number[]
}

export const detectionService = {
  getLatestDetection(): DetectionResult {
    return {
      batchId: 'OB-2407-018',
      totalDetected: 428,
      avgConfidence: '94.6%',
      imagesAnalyzed: 12,
      imagesProcessed: '12 / 12',
      sparklineValues: [20, 35, 28, 45, 42, 59, 54]
    }
  },
  getDetectionForBatch(batchId: string, applesCount: number, imageCount: number): DetectionResult {
    return {
      batchId,
      totalDetected: applesCount,
      avgConfidence: '94.6%',
      imagesAnalyzed: imageCount,
      imagesProcessed: `${imageCount} / ${imageCount}`,
      sparklineValues: [20, 35, 28, 45, 42, 59, 54]
    }
  }
}
