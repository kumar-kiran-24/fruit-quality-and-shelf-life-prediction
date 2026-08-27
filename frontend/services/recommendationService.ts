export interface BuyerMatch {
  name: string
  location: string
  matchScore: string
  distance: string
}

export interface Recommendation {
  batchId: string
  travelExplanation: string
  matches: BuyerMatch[]
}

const RECOMMENDATIONS_MAP: Record<string, Recommendation> = {
  'OB-2407-018': {
    batchId: 'OB-2407-018',
    travelExplanation: 'This batch can travel up to 280 miles and arrive with 14+ days remaining.',
    matches: [
      { name: 'FreshFields Market', location: 'Portland, OR', matchScore: '96% match', distance: '12 mi' },
      { name: 'Harvest & Co.', location: 'Seattle, WA', matchScore: '88% match', distance: '184 mi' },
      { name: 'Green Basket', location: 'Boise, ID', matchScore: '76% match', distance: '280 mi' }
    ]
  },
  'OB-2407-017': {
    batchId: 'OB-2407-017',
    travelExplanation: 'This batch has moderate freshness and is ideal for short distance shipping (within 100 miles).',
    matches: [
      { name: 'FreshFields Market', location: 'Portland, OR', matchScore: '92% match', distance: '12 mi' },
      { name: 'Valley Foods', location: 'Eugene, OR', matchScore: '82% match', distance: '78 mi' }
    ]
  },
  'OB-2407-016': {
    batchId: 'OB-2407-016',
    travelExplanation: 'Outstanding shelf life allows for long distance transport (up to 400 miles) and maximum flexibility.',
    matches: [
      { name: 'Harvest & Co.', location: 'Seattle, WA', matchScore: '98% match', distance: '184 mi' },
      { name: 'Green Basket', location: 'Boise, ID', matchScore: '89% match', distance: '280 mi' },
      { name: 'FreshFields Market', location: 'Portland, OR', matchScore: '85% match', distance: '12 mi' }
    ]
  },
  'OB-2407-015': {
    batchId: 'OB-2407-015',
    travelExplanation: 'Freshness window is critical (9 days). Urgent delivery within local Portland area is required.',
    matches: [
      { name: 'FreshFields Market', location: 'Portland, OR', matchScore: '95% match', distance: '12 mi' },
      { name: 'Valley Foods', location: 'Eugene, OR', matchScore: '60% match', distance: '78 mi' }
    ]
  }
}

export const recommendationService = {
  getRecommendationForBatch(batchId: string): Recommendation {
    if (RECOMMENDATIONS_MAP[batchId]) {
      return RECOMMENDATIONS_MAP[batchId]
    }
    return {
      batchId,
      travelExplanation: 'Dynamic analysis matches this batch to nearby grocers for immediate stock placement.',
      matches: [
        { name: 'FreshFields Market', location: 'Portland, OR', matchScore: '90% match', distance: '12 mi' },
        { name: 'Valley Foods', location: 'Eugene, OR', matchScore: '75% match', distance: '78 mi' }
      ]
    }
  }
}
