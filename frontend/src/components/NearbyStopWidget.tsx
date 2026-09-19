import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchNearbyStops,
  fetchStopDepartures,
  type NearbyStop,
  type StopDeparture,
} from '@/lib/api'
import { listOfflineCities, type OfflineCity } from '@/lib/offlineStorage'
import { getCurrentLocation } from '@/lib/geolocation'
import {
  CATCH_BUFFER_MIN,
  clockAfter,
  firstCatchable,
  liveMinutesAhead,
} from '@/lib/departureTime'
import StopDetailSheet from '@/components/StopDetailSheet'

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`
  const km = meters / 1000
  return `${km.toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`
}

function timeText(minutes: number): string {
  if (minutes <= 0) return 'şimdi'
  return `${minutes} dk`
}

/** Yuruyus suresi (dk). Konservatif 1.0 m/s = 60 m/dk. */
function walkMinutes(distanceM: number): number {
  return Math.max(1, Math.ceil(distanceM / 60))
}

/** Kullanicinin en yakin duraktan sonraki kalkisa yetisip yetismeyecegini hesaplar.
 * minutes cihaz saatine gore guncellenir (liveAhead); varis saati Istanbul
 * duvar saatiyle gosterilir. Tum sureler tahminidir. */
function leaveDecision(
  stop: NearbyStop,
  departure: StopDeparture,
  nowMs: number,
): { text: string; sub: string; urgent: boolean } {
  const walk = walkMinutes(stop.distance_m)
  const ahead = liveMinutesAhead(departure, nowMs)
  const arrival = clockAfter(nowMs, walk)
  const headStart = ahead - walk

  if (headStart <= 0) {
    return {
      text: 'Hemen çık!',
      sub: `Durağa yürüyüşün ~${walk} dk (tahmini), kalkışa ${Math.max(0, ahead)} dk var.`,
      urgent: true,
    }
  }

  if (headStart <= 3) {
    return {
      text: `Yaklaşık ${headStart} dk içinde çık`,
      sub: `~${arrival} gibi durakta olursun (tahmini). ${departure.line} ${departure.time}'te kalkıyor, ~${ahead} dk var.`,
      urgent: true,
    }
  }

  return {
    text: `${headStart} dk daha bekleyebilirsin`,
    sub: `~${arrival} gibi durakta olursun (tahmini). ${departure.line} ${departure.time}'te kalkıyor, ~${ahead} dk var.`,
    urgent: false,
  }
}

/** Indirilen cevrimdisi veriden en yakin duraklari hesaplar. */
async function nearestFromOffline(
  lat: number,
  lon: number,
  limit = 5,
): Promise<(NearbyStop & { offline?: boolean })[]> {
  let cities: OfflineCity[]
  try {
    cities = await listOfflineCities()
  } catch {
    return []
  }
  if (!cities.length) return []

  const all: (NearbyStop & { offline?: boolean })[] = []
  for (const c of cities) {
    for (const s of c.stops as { id?: string; name: string; lat: number; lon: number; lines?: { n: string }[] }[]) {
      const dx = (s.lon - lon) * 111320 * Math.cos(((lat + s.lat) / 2) * (Math.PI / 180))
      const dy = (s.lat - lat) * 111320
      const dist = Math.sqrt(dx * dx + dy * dy)
      all.push({
        city: c.city,
        name: s.name,
        stop_id: s.id ?? '',
        lat: s.lat,
        lon: s.lon,
        distance_m: dist,
        lines: (s.lines ?? []).map((l) => l.n).slice(0, 12),
        offline: true,
      })
    }
  }
  all.sort((a, b) => a.distance_m - b.distance_m)
  return all.slice(0, limit)
}

export default function NearbyStopWidget(): ReactElement {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stop, setStop] = useState<NearbyStop | null>(null)
  const [departures, setDepartures] = useState<StopDeparture[] | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  // Gercek cihaz saati: kalan sureler her 30 sn'de yeniden hesaplanir.
  const [nowMs, setNowMs] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNowMs(Date.now()), 30000)
    return () => clearInterval(timer)
  }, [])

  function detect() {
    setLoading(true)
    setError(null)

    getCurrentLocation()
      .then(async (res) => {
        if (!res.ok) {
          setError(res.message)
          setLoading(false)
          return
        }

        const lat = res.coords.lat
        const lon = res.coords.lon

        try {
          let results = await fetchNearbyStops(lat, lon, 5)
          let offlineMode = false

          // Sunucuya ulasilamiyorsa indirilmis sehir verisinden hesapla
          if (results === null) {
            const off = await nearestFromOffline(lat, lon, 5)
            if (off.length) {
              results = off
              offlineMode = true
            }
          }

          const nearest = results?.[0] ?? null
          setStop(nearest)

          if (nearest && !offlineMode) {
            const deps = await fetchStopDepartures(
              nearest.city,
              nearest.name,
              nearest.lat,
              nearest.lon,
              nearest.lines,
            )
            setDepartures(deps ?? [])
            setNowMs(Date.now())
          } else if (nearest && offlineMode) {
            setDepartures([])
          }
        } catch (e) {
          setError('Durak bilgisi alınamadı.')
        } finally {
          setLoading(false)
        }
      })
  }

  useEffect(() => {
    detect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (detailOpen && stop) {
    return (
      <StopDetailSheet
        stop={stop}
        onClose={() => setDetailOpen(false)}
        onPlanTo={() => setDetailOpen(false)}
      />
    )
  }

  if (error) {
    return (
      <button
        type="button"
        onClick={detect}
        className="mt-4 flex w-full items-center gap-3 rounded-2xl border border-line bg-surface-2/90 p-4 text-left"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">📍</span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold">En yakın durağı görmek için konum izni ver</p>
          <p className="text-xs text-muted">Kapat ve tekrar dene</p>
        </div>
      </button>
    )
  }

  if (loading || !stop) {
    return (
      <div className="mt-4 rounded-2xl border border-line bg-surface-2/90 p-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent/10 text-accent">📍</span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold">En yakın durak aranıyor…</p>
          </div>
        </div>
      </div>
    )
  }

  // Gecmis seferleri ele (cihaz saatine gore canli), hat basi ilkini goster.
  const liveDepartures = (departures ?? []).filter((d) => liveMinutesAhead(d, nowMs) >= 0)
  const firstByLine = new Map<string, StopDeparture>()
  if (departures) {
    for (const d of liveDepartures) {
      if (!firstByLine.has(d.line)) firstByLine.set(d.line, d)
    }
  }

  // Yetisilemeyecek otobus onerme: yurume + guvenlik payini karsilayan ilk sefer.
  const walkForDecision = stop ? walkMinutes(stop.distance_m) : 0
  const catchable = stop
    ? firstCatchable(liveDepartures, walkForDecision, CATCH_BUFFER_MIN, nowMs)
    : null
  const decision =
    stop && catchable ? leaveDecision(stop, catchable, nowMs) : null
  const nothingCatchable =
    stop && departures !== null && liveDepartures.length > 0 && !catchable

  return (
    <button
      type="button"
      onClick={() => setDetailOpen(true)}
      className="mt-4 w-full rounded-2xl border border-line bg-surface-2/90 p-4 text-left transition-colors hover:border-accent/50"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-wide text-muted">En yakın durak</p>
          <p className="mt-0.5 truncate text-base font-bold">{stop.name}</p>
          <p className="text-xs text-muted">
            {stop.city} · {formatDistance(stop.distance_m)}
            {(stop as { offline?: boolean }).offline && ' · çevrimdışı'}
          </p>
        </div>
        <span className="shrink-0 rounded-full bg-accent/10 px-2 py-1 text-xs font-bold text-accent">Detay</span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {Array.from(firstByLine.values()).slice(0, 4).map((d) => (
          <span
            key={d.line}
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
              d.source === 'tahmini'
                ? 'bg-bg/60 italic text-muted'
                : 'bg-accent/15 text-accent'
            }`}
          >
            {d.line}
            <span className="tabular-nums">{timeText(liveMinutesAhead(d, nowMs))}</span>
          </span>
        ))}
        {departures !== null && firstByLine.size === 0 && (
          <span className="text-xs text-muted">Otobüs saat bilgisi şu anda güncel değil.</span>
        )}
      </div>

      {nothingCatchable && (
        <div className="mt-3 rounded-xl border border-line bg-surface p-3">
          <p className="text-sm font-bold">🕐 Yürüyerek yetişebileceğin sefer yok</p>
          <p className="mt-0.5 text-xs text-fg/80">
            listedeki seferler yürüme sürene yetişmiyor. Sonraki seferler için Detay'a bak.
          </p>
        </div>
      )}

      {decision && (
        <div
          className={`mt-3 rounded-xl border p-3 ${
            decision.urgent
              ? 'border-amber-500/30 bg-amber-500/10'
              : 'border-emerald-500/30 bg-emerald-500/10'
          }`}
        >
          <p
            className={`text-sm font-bold ${
              decision.urgent ? 'text-amber-300' : 'text-emerald-300'
            }`}
          >
            {decision.urgent ? '⏰' : '✅'} {decision.text}
          </p>
          <p className="mt-0.5 text-xs text-fg/80">{decision.sub}</p>
        </div>
      )}
    </button>
  )
}
