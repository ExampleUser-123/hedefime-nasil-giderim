import {
  addTarget as apiAddTarget,
  deleteTarget as apiDeleteTarget,
  fetchTargets as apiFetchTargets,
  postGameEvent,
  type GameTarget,
} from './api'
import { getStoredUser } from './auth'

const LOCAL_TARGETS_KEY = 'hng-local-targets'

function readLocal(): GameTarget[] {
  try {
    const raw = localStorage.getItem(LOCAL_TARGETS_KEY)
    const arr = raw ? JSON.parse(raw) : []
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function writeLocal(targets: GameTarget[]) {
  try {
    localStorage.setItem(LOCAL_TARGETS_KEY, JSON.stringify(targets))
  } catch {
    // sessizce gec
  }
}

/** Giris yapilmissa XP olayi gonderir; degilse/yoksa sessizce null. */
export async function award(event: string, meta: Record<string, unknown> = {}) {
  if (!getStoredUser()) return null
  try {
    return await postGameEvent(event, meta)
  } catch {
    return null
  }
}

/** Hedefler: girisliyse backend, degilse localStorage. */
export async function loadTargets(): Promise<GameTarget[]> {
  if (getStoredUser()) {
    const remote = await apiFetchTargets()
    // backend bos donerse local'i ezme; ikisini birlestirme (cift kayit onlenir)
    if (remote.length > 0 || readLocal().length === 0) return remote
    return remote
  }
  return readLocal()
}

export async function saveTarget(t: {
  name: string; lat?: number | null; lon?: number | null; address?: string; city?: string
}): Promise<GameTarget[]> {
  if (getStoredUser()) {
    const res = await apiAddTarget(t)
    if (res) {
      await award('target_added')
      return res.targets
    }
    return loadTargets()
  }
  const list = readLocal()
  if (list.length >= 50) return list
  list.push({
    id: `local-${Date.now()}`,
    name: t.name.slice(0, 80),
    address: t.address ?? '',
    city: t.city ?? '',
    lat: t.lat ?? null,
    lon: t.lon ?? null,
    created_at: new Date().toISOString(),
  })
  writeLocal(list)
  return list
}

export async function removeTarget(id: string): Promise<GameTarget[]> {
  if (getStoredUser()) {
    const res = await apiDeleteTarget(id)
    if (res) return res.targets
    return loadTargets()
  }
  const list = readLocal().filter((t) => t.id !== id)
  writeLocal(list)
  return list
}
