import { useEffect, useState, type ReactElement } from 'react'
import { fetchXpStore } from '@/lib/api'
import { getStoredUser } from '@/lib/auth'

type Cafe = { name: string; lat: number; lon: number; dist_m: number }

function haversineM(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const r = 6371000
  const p1 = (lat1 * Math.PI) / 180
  const p2 = (lat2 * Math.PI) / 180
  const dp = ((lat2 - lat1) * Math.PI) / 180
  const dl = ((lon2 - lon1) * Math.PI) / 180
  const a = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2
  return 2 * r * Math.asin(Math.sqrt(a))
}

/**
 * XP Magazasi cafe_filter urunu: baslangic cev resindeki kafe/mola
 * noktalarini acik harita verisiyle (OSM Overpass) listeler.
 * Puan siralamasi yok (ucretsiz veride puan bulunmaz); mesafeye gore siralanir.
 */
export default function CafeStops({
  lat,
  lon,
}: {
  lat?: number
  lon?: number
}): ReactElement {
  const [owned, setOwned] = useState<boolean | null>(null)
  const [cafes, setCafes] = useState<Cafe[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!getStoredUser()) {
      setOwned(false)
      return
    }
    fetchXpStore()
      .then((data) => {
        setOwned(data.items.some((i) => i.id === 'cafe_filter' && i.owned))
      })
      .catch(() => setOwned(false))
  }, [])

  useEffect(() => {
    if (owned !== true || lat == null || lon == null) return
    let alive = true
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 20000)
    ;(async () => {
      try {
        const query = `[out:json][timeout:15];node["amenity"="cafe"](around:1200,${lat},${lon});out center 20;`
        const res = await fetch('https://overpass-api.de/api/interpreter', {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'data=' + encodeURIComponent(query),
          signal: controller.signal,
        })
        const data = (await res.json()) as {
          elements?: { lat?: number; lon?: number; tags?: { name?: string } }[]
        }
        const list: Cafe[] = (data.elements ?? [])
          .filter((e) => e.lat != null && e.lon != null)
          .map((e) => ({
            name: e.tags?.name ?? 'Kafe',
            lat: e.lat as number,
            lon: e.lon as number,
            dist_m: haversineM(lat, lon, e.lat as number, e.lon as number),
          }))
          .sort((a, b) => a.dist_m - b.dist_m)
          .slice(0, 5)
        if (alive) setCafes(list)
      } catch {
        if (alive) setError(true)
      } finally {
        clearTimeout(timer)
      }
    })()
    return () => {
      alive = false
      clearTimeout(timer)
      controller.abort()
    }
  }, [owned, lat, lon])

  if (owned !== true) return <></>

  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-xs font-bold">
        ☕ Yakındaki kafe &amp; mola noktaları{' '}
        <span className="font-normal text-muted">(açık harita verisi, puansız)</span>
      </p>
      {cafes === null && !error && (
        <p className="mt-2 text-xs text-muted">Çevre taranıyor…</p>
      )}
      {error && (
        <p className="mt-2 text-xs text-muted">Çevre şu anda taranamadı. İnterneti kontrol edip tekrar dene.</p>
      )}
      {cafes !== null && cafes.length === 0 && !error && (
        <p className="mt-2 text-xs text-muted">1,2 km çevrede kayıtlı kafe bulunamadı.</p>
      )}
      {cafes !== null && cafes.length > 0 && (
        <ul className="mt-2 space-y-1.5">
          {cafes.map((c, i) => (
            <li key={`${c.name}-${i}`} className="flex items-center justify-between gap-2 rounded-xl bg-bg/40 px-3 py-2">
              <p className="min-w-0 truncate text-xs font-bold">{c.name}</p>
              <span className="shrink-0 text-[11px] text-muted tabular-nums">
                {c.dist_m < 1000 ? `${Math.round(c.dist_m)} m` : `${(c.dist_m / 1000).toFixed(1).replace('.', ',')} km`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
