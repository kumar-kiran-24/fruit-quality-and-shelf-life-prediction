// ============================================================
// FEFO CONFIGURATION
//
// Centralized configuration for First Expiry, First Out
// dispatch planning. All thresholds and helpers live here
// so they can be easily replaced by backend logic later.
// ============================================================

// ============================================================
// SHELF-LIFE → DAYS MAPPING
//
// Maps backend shelf-life prediction labels to estimated
// remaining days. Keys must match the backend model outputs.
// ============================================================

export const SHELF_LIFE_DAYS_MAP: Record<string, number> = {
  '1-5 days': 3,
  '5-10 days': 7,
  '10-14 days': 12,
}

// ============================================================
// FEFO PRIORITY THRESHOLDS
//
// Defines the boundaries between priority levels.
// All values are in remaining shelf-life days.
// Lower days = higher urgency.
//
// To change behavior, adjust these numbers only.
// ============================================================

export const FEFO_THRESHOLDS = {
  /** 0–2 days remaining → Send Today */
  URGENT: 2,
  /** 3–5 days remaining → Prioritize Today / Tomorrow */
  HIGH: 5,
  /** 6–10 days remaining → Schedule Soon */
  MEDIUM: 10,
  // Above MEDIUM → NORMAL / Upcoming
}

// ============================================================
// PRIORITY LEVEL DEFINITIONS
// ============================================================

export interface FefoPriority {
  label: string
  color: string
  bgColor: string
  sortOrder: number
  dispatchWindow: DispatchWindow
  actionLabel: string
}

export type DispatchWindow = 'today' | 'tomorrow' | 'upcoming' | 'pending'

export const PRIORITY_LEVELS: Record<string, FefoPriority> = {
  URGENT: {
    label: 'URGENT',
    color: '#b91c1c',
    bgColor: '#fee2e2',
    sortOrder: 1,
    dispatchWindow: 'today',
    actionLabel: 'Dispatch immediately',
  },
  HIGH: {
    label: 'HIGH',
    color: '#c2410c',
    bgColor: '#ffedd5',
    sortOrder: 2,
    dispatchWindow: 'tomorrow',
    actionLabel: 'Reserve transport',
  },
  MEDIUM: {
    label: 'MEDIUM',
    color: '#92400e',
    bgColor: '#fef3c7',
    sortOrder: 3,
    dispatchWindow: 'upcoming',
    actionLabel: 'Schedule delivery',
  },
  NORMAL: {
    label: 'NORMAL',
    color: '#166534',
    bgColor: '#dcfce7',
    sortOrder: 4,
    dispatchWindow: 'upcoming',
    actionLabel: 'Monitor and schedule',
  },
  PENDING: {
    label: 'PENDING',
    color: '#71808a',
    bgColor: '#eeeDE8',
    sortOrder: 5,
    dispatchWindow: 'pending',
    actionLabel: 'Awaiting analysis',
  },
}

// ============================================================
// SHELF-LIFE LABELS
// ============================================================

export const DISPATCH_WINDOW_LABELS: Record<DispatchWindow, { title: string; subtitle: string; icon: string }> = {
  today: { title: 'Send Today', subtitle: 'Most urgent — dispatch immediately', icon: '🔴' },
  tomorrow: { title: 'Send Tomorrow', subtitle: 'High priority — plan transport now', icon: '🟠' },
  upcoming: { title: 'Upcoming Dispatches', subtitle: 'Schedule within the next few days', icon: '🟢' },
  pending: { title: 'Awaiting Shelf-Life Analysis', subtitle: 'Run shelf-life prediction first', icon: '⚪' },
}

// ============================================================
// HELPER: PARSE REMAINING DAYS
// ============================================================

/**
 * Parse a shelf-life prediction label into estimated remaining days.
 * Returns null if the label is missing, unknown, or not a string.
 */
export function parseRemainingDays(label: string | null | undefined): number | null {
  if (!label || typeof label !== 'string') return null
  if (SHELF_LIFE_DAYS_MAP[label] !== undefined) return SHELF_LIFE_DAYS_MAP[label]
  // Fallback: try to extract the first number from the label
  const match = label.match(/(\d+)/)
  if (match) return parseInt(match[1], 10)
  return null
}

// ============================================================
// HELPER: DERIVE FEFO PRIORITY
// ============================================================

/**
 * Derive FEFO priority level from remaining shelf-life days.
 * Uses centralized FEFO_THRESHOLDS.
 */
export function deriveFefoPriority(days: number | null): FefoPriority {
  if (days === null) return PRIORITY_LEVELS.PENDING
  if (days <= FEFO_THRESHOLDS.URGENT) return PRIORITY_LEVELS.URGENT
  if (days <= FEFO_THRESHOLDS.HIGH) return PRIORITY_LEVELS.HIGH
  if (days <= FEFO_THRESHOLDS.MEDIUM) return PRIORITY_LEVELS.MEDIUM
  return PRIORITY_LEVELS.NORMAL
}

// ============================================================
// HELPER: GET DISPATCH WINDOW
// ============================================================

/**
 * Determine the dispatch window for a batch based on remaining days.
 */
export function getDispatchWindow(days: number | null): DispatchWindow {
  if (days === null) return 'pending'
  if (days <= FEFO_THRESHOLDS.URGENT) return 'today'
  if (days <= FEFO_THRESHOLDS.HIGH) return 'tomorrow'
  return 'upcoming'
}

// ============================================================
// HELPER: FEFO ACTION MESSAGE
// ============================================================

/**
 * Generate a recommended action message based on FEFO priority.
 */
export function getFefoActionMsg(priority: string, days: number | null): string {
  if (days === null) return 'Awaiting shelf-life analysis'
  switch (priority) {
    case 'URGENT': return 'Prioritize immediate dispatch to minimize spoilage risk'
    case 'HIGH': return 'Reserve transport capacity and plan dispatch'
    case 'MEDIUM': return 'Schedule delivery within the next few days'
    case 'NORMAL': return 'Monitor freshness and schedule when convenient'
    default: return 'Process this batch soon'
  }
}

// ============================================================
// DESTINATION / BUYER CATALOG
//
// Frontend catalog of destination locations around Karnataka
// and nearby major markets. Used as fallback/demo data when
// real backend buyer/location data is not available.
//
// Each destination supports: name, city, state, latitude,
// longitude, distance_km (estimated from a reference origin),
// and destination_type.
//
// To replace with backend data, override with API results
// and keep this catalog as a fallback only.
// ============================================================

export interface DestinationCatalog {
  id: string
  name: string
  city: string
  state: string
  latitude: number
  longitude: number
  distance_km: number
  destination_type: string
}

/**
 * Reference origin point for distance estimation.
 * Should match the orchard's registered location.
 */
export const REFERENCE_ORIGIN = {
  name: 'Hawthorne Orchards',
  latitude: 12.9716,
  longitude: 77.5946,
}

/**
 * Frontend destination catalog — Karnataka region.
 * Distances are approximate from the reference origin.
 */
export const DESTINATION_CATALOG: DestinationCatalog[] = [
  {
    id: 'DEST-BLR-001',
    name: 'Bengaluru Fresh Market',
    city: 'Bengaluru',
    state: 'Karnataka',
    latitude: 12.9716,
    longitude: 77.5946,
    distance_km: 0,
    destination_type: 'Fresh Market',
  },
  {
    id: 'DEST-MYS-001',
    name: 'Mysuru Fruit Market',
    city: 'Mysuru',
    state: 'Karnataka',
    latitude: 12.2958,
    longitude: 76.6394,
    distance_km: 150,
    destination_type: 'Fruit Market',
  },
  {
    id: 'DEST-HUB-001',
    name: 'Hubballi Agricultural Market',
    city: 'Hubballi',
    state: 'Karnataka',
    latitude: 15.3647,
    longitude: 75.1240,
    distance_km: 410,
    destination_type: 'Agricultural Market',
  },
  {
    id: 'DEST-MNG-001',
    name: 'Mangaluru Fresh Produce Market',
    city: 'Mangaluru',
    state: 'Karnataka',
    latitude: 12.9141,
    longitude: 74.8560,
    distance_km: 350,
    destination_type: 'Fresh Produce Market',
  },
  {
    id: 'DEST-SHG-001',
    name: 'Shivamogga Fruit Market',
    city: 'Shivamogga',
    state: 'Karnataka',
    latitude: 13.9299,
    longitude: 75.5681,
    distance_km: 280,
    destination_type: 'Fruit Market',
  },
  {
    id: 'DEST-DVG-001',
    name: 'Davanagere Agricultural Market',
    city: 'Davanagere',
    state: 'Karnataka',
    latitude: 14.4644,
    longitude: 75.9216,
    distance_km: 245,
    destination_type: 'Agricultural Market',
  },
  {
    id: 'DEST-TMK-001',
    name: 'Tumakuru Wholesale Market',
    city: 'Tumakuru',
    state: 'Karnataka',
    latitude: 13.3409,
    longitude: 77.1010,
    distance_km: 85,
    destination_type: 'Wholesale Market',
  },
  {
    id: 'DEST-HSN-001',
    name: 'Hassan Produce Market',
    city: 'Hassan',
    state: 'Karnataka',
    latitude: 13.0076,
    longitude: 76.0976,
    distance_km: 195,
    destination_type: 'Produce Market',
  },
  {
    id: 'DEST-BLG-001',
    name: 'Belagavi Fruit Market',
    city: 'Belagavi',
    state: 'Karnataka',
    latitude: 15.8497,
    longitude: 74.4977,
    distance_km: 500,
    destination_type: 'Fruit Market',
  },
  {
    id: 'DEST-CMR-001',
    name: 'Chikkamagaluru Fresh Market',
    city: 'Chikkamagaluru',
    state: 'Karnataka',
    latitude: 13.3162,
    longitude: 75.7725,
    distance_km: 250,
    destination_type: 'Fresh Market',
  },
]

// ============================================================
// HELPER: MATCH DESTINATIONS TO BATCH
//
// Given a batch with remaining shelf-life days, returns
// destinations ranked by suitability for the dispatch window.
// This is frontend-only logic that can later be replaced by
// backend recommendation results.
// ============================================================

export function matchDestinationsForBatch(
  days: number | null,
  batchOrigin?: string
): (DestinationCatalog & { dispatchFit: string; fitPriority: number })[] {
  const window = getDispatchWindow(days)

  // Sort destinations by distance (nearest first for urgent, flexible for normal)
  const ranked = DESTINATION_CATALOG.map(dest => {
    let fitPriority: number
    let dispatchFit: string

    if (window === 'today') {
      // Urgent: prefer nearby destinations (shorter transit)
      fitPriority = dest.distance_km <= 150 ? 1 : dest.distance_km <= 300 ? 2 : 3
      dispatchFit = fitPriority === 1 ? 'Send Today' : 'Send Today (longer transit)'
    } else if (window === 'tomorrow') {
      // High: moderate distance acceptable
      fitPriority = dest.distance_km <= 300 ? 1 : dest.distance_km <= 500 ? 2 : 3
      dispatchFit = fitPriority === 1 ? 'Send Tomorrow' : 'Send Tomorrow (longer transit)'
    } else {
      // Normal/upcoming: any destination works
      fitPriority = 1
      dispatchFit = 'Schedule'
    }

    return { ...dest, dispatchFit, fitPriority }
  })

  // Sort by fitPriority, then by distance
  ranked.sort((a, b) => a.fitPriority - b.fitPriority || a.distance_km - b.distance_km)

  return ranked
}

// ============================================================
// HELPER: SAFE NUMBER ACCESS
// ============================================================

/**
 * Safely access a numeric value, returning null for
 * undefined, null, NaN, or non-numeric strings.
 */
export function safeNumeric(value: any): number | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return isNaN(value) ? null : value
  if (typeof value === 'string') {
    const num = parseFloat(value)
    return isNaN(num) ? null : num
  }
  return null
}
