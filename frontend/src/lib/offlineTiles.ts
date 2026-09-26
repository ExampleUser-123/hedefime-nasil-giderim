/** Cevrimdisi harita karolari (XP Magazasi offline_map urunu).
 * Yakin cevre z15+z16 karolari IndexedDB'ye alinir; harita katmani once
 * yerelden okur, bulamazsa agdan ceker. Kucuk tutulur (~35 karo, birkac MB).
 */

const DB_NAME = 'hng-tiles'
const STORE = 'tiles'
const META_KEY = 'hng-tile-pack'

export type TilePackMeta = {
  lat: number
  lon: number
  count: number
  at: number
}

function lonToX(lon: number, z: number): number {
  return Math.floor(((lon + 180) / 360) * 2 ** z)
}

function latToY(lat: number, z: number): number {
  const rad = (lat * Math.PI) / 180
  return Math.floor(
    ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * 2 ** z,
  )
}

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1)
    req.onupgradeneeded = () => {
      req.result.createObjectStore(STORE)
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function getTileBlob(z: number, x: number, y: number): Promise<Blob | null> {
  try {
    const db = await openDB()
    return await new Promise((resolve) => {
      const tx = db.transaction(STORE, 'readonly')
      const req = tx.objectStore(STORE).get(`${z}/${x}/${y}`)
      req.onsuccess = () => resolve((req.result as Blob | undefined) ?? null)
      req.onerror = () => resolve(null)
    })
  } catch {
    return null
  }
}

async function putTile(z: number, x: number, y: number, blob: Blob): Promise<void> {
  const db = await openDB()
  await new Promise<void>((resolve) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).put(blob, `${z}/${x}/${y}`)
    tx.oncomplete = () => resolve()
    tx.onerror = () => resolve()
  })
}

export function getPackMeta(): TilePackMeta | null {
  try {
    const raw = localStorage.getItem(META_KEY)
    if (!raw) return null
    const meta = JSON.parse(raw) as TilePackMeta
    if (typeof meta.lat !== 'number' || typeof meta.count !== 'number') return null
    return meta
  } catch {
    return null
  }
}

function setPackMeta(meta: TilePackMeta | null): void {
  try {
    if (meta) localStorage.setItem(META_KEY, JSON.stringify(meta))
    else localStorage.removeItem(META_KEY)
  } catch {
    // sessiz gec
  }
}

export async function clearPack(): Promise<void> {
  try {
    const db = await openDB()
    await new Promise<void>((resolve) => {
      const tx = db.transaction(STORE, 'readwrite')
      tx.objectStore(STORE).clear()
      tx.oncomplete = () => resolve()
      tx.onerror = () => resolve()
    })
  } catch {
    // sessiz gec
  }
  setPackMeta(null)
}

/** Merkez cevresini indir: z15'te 3x3, z16'da 5x5 karo (~34 PNG). */
export async function downloadPack(
  lat: number,
  lon: number,
  onProgress?: (done: number, total: number) => void,
): Promise<{ count: number }> {
  const jobs: { z: number; x: number; y: number }[] = []
  for (const [z, r] of [[15, 1], [16, 2]] as const) {
    const cx = lonToX(lon, z)
    const cy = latToY(lat, z)
    for (let dx = -r; dx <= r; dx++) {
      for (let dy = -r; dy <= r; dy++) {
        jobs.push({ z, x: cx + dx, y: cy + dy })
      }
    }
  }

  let done = 0
  // Sirali indir (karo sunucusunu bogmamak icin)
  for (const [i, job] of jobs.entries()) {
    try {
      const sub = 'abc'[i % 3]
      const res = await fetch(
        `https://${sub}.tile.openstreetmap.org/${job.z}/${job.x}/${job.y}.png`,
      )
      if (res.ok) {
        const blob = await res.blob()
        if (blob.size > 0) {
          await putTile(job.z, job.x, job.y, blob)
          done += 1
        }
      }
    } catch {
      // tek karo patlarsa devam
    }
    onProgress?.(i + 1, jobs.length)
  }

  setPackMeta({ lat, lon, count: done, at: Date.now() })
  return { count: done }
}
