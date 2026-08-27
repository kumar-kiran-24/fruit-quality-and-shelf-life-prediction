export interface Buyer {
  name: string
  location: string
  type: string
  orders: string
}

const DEFAULT_BUYERS: Buyer[] = [
  { name: 'FreshFields Market', location: 'Portland, OR', type: 'Produce retailer', orders: '12 active orders' },
  { name: 'Harvest & Co.', location: 'Seattle, WA', type: 'Wholesale distributor', orders: '8 active orders' },
  { name: 'Green Basket', location: 'Boise, ID', type: 'Organic grocer', orders: '4 active orders' },
  { name: 'Valley Foods', location: 'Eugene, OR', type: 'Local market', orders: 'No active orders' }
]

export const buyerService = {
  getBuyers(): Buyer[] {
    return DEFAULT_BUYERS
  }
}
