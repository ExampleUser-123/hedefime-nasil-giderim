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
const MAX_ITEMS = 20

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
