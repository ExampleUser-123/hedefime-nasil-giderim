export type SavedRoute = {
  from: string
  to: string
  people: number
  mode: string
  savedAt: number
}

export type HistoryEntry = SavedRoute

const HISTORY_KEY = 'hng-history'
const SAVED_KEY = 'hng-saved'
const COORDS_KEY = 'hng-last-coords'
const MAX_ITEMS = 20

export type LastCoords = { lat: number; lon: number }

export function saveLastCoords(lat: number, lon: number) {
  try {
    localStorage.setItem(COORDS_KEY, JSON.stringify({ lat, lon, at: Date.now() }))
  } catch {
    // localStorage kapaliysa sessizce devam
  }
}

export function getLastCoords(): LastCoords | null {
  try {
    const raw = localStorage.getItem(COORDS_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as LastCoords & { at: number }
    if (typeof parsed.lat !== 'number' || typeof parsed.lon !== 'number') return null
    // 24 saatten eski konum guncel olmayabilir
    if (Date.now() - parsed.at > 24 * 3600 * 1000) return null
    return { lat: parsed.lat, lon: parsed.lon }
  } catch {
    return null
  }
}

function readList(key: string): SavedRoute[] {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function writeList(key: string, list: SavedRoute[]) {
  try {
    localStorage.setItem(key, JSON.stringify(list))
  } catch {
    // localStorage kapalıysa sessizce devam
  }
}

export function getHistory(): HistoryEntry[] {
  return readList(HISTORY_KEY)
}

export function addHistory(entry: Omit<SavedRoute, 'savedAt'>) {
  const rest = readList(HISTORY_KEY).filter(
    (item) => !(item.from === entry.from && item.to === entry.to),
  )
  writeList(HISTORY_KEY, [{ ...entry, savedAt: Date.now() }, ...rest].slice(0, MAX_ITEMS))
}

export function getSaved(): SavedRoute[] {
  return readList(SAVED_KEY)
}

export function isSaved(from: string, to: string): boolean {
  return getSaved().some((item) => item.from === from && item.to === to)
}

export function toggleSaved(entry: Omit<SavedRoute, 'savedAt'>): boolean {
  const current = getSaved()
  const exists = current.some(
    (item) => item.from === entry.from && item.to === entry.to,
  )

  if (exists) {
    writeList(
      SAVED_KEY,
      current.filter((item) => !(item.from === entry.from && item.to === entry.to)),
    )
    return false
  }

  writeList(SAVED_KEY, [{ ...entry, savedAt: Date.now() }, ...current].slice(0, MAX_ITEMS))
  return true
}

export function removeSaved(from: string, to: string) {
  writeList(
    SAVED_KEY,
    getSaved().filter((item) => !(item.from === from && item.to === to)),
  )
}

export function clearHistory() {
  writeList(HISTORY_KEY, [])
}

// --- Ev / İş sabit konumları ------------------------------------------------

export type PinnedPlace = {
  label: string
  address: string
  lat: number
  lon: number
}

const HOME_KEY = 'hng-home-place'
const WORK_KEY = 'hng-work-place'

export function getPinnedPlace(kind: 'home' | 'work'): PinnedPlace | null {
  try {
    const raw = localStorage.getItem(kind === 'home' ? HOME_KEY : WORK_KEY)
    if (!raw) return null

    const parsed = JSON.parse(raw) as PinnedPlace

    if (
      typeof parsed.lat !== 'number' ||
      typeof parsed.lon !== 'number' ||
      !parsed.label
    ) {
      return null
    }

    return parsed
  } catch {
    return null
  }
}

export function setPinnedPlace(kind: 'home' | 'work', place: PinnedPlace) {
  try {
    localStorage.setItem(kind === 'home' ? HOME_KEY : WORK_KEY, JSON.stringify(place))
  } catch {
    // sessizce devam
  }
}

export function clearPinnedPlace(kind: 'home' | 'work') {
  try {
    localStorage.removeItem(kind === 'home' ? HOME_KEY : WORK_KEY)
  } catch {
    // sessizce devam
  }
}
