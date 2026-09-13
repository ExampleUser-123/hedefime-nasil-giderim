import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchNearbyStops,
  fetchStopDepartures,
  type NearbyStop,
  type StopDeparture,
} from '@/lib/api'
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

export default function NearbyStopWidget(): ReactElement {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stop, setStop] = useState<NearbyStop | null>(null)
  const [departures, setDepartures] = useState<StopDeparture[] | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  function detect() {
    if (!('geolocation' in navigator)) {
      setError('Cihazın konum desteği sunmuyor.')
      return
    }

    setLoading(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude
        const lon = position.coords.longitude

        try {
          const results = await fetchNearbyStops(lat, lon, 5)
          const nearest = results?.[0] ?? null
          setStop(nearest)

          if (nearest) {
            const deps = await fetchStopDepartures(
              nearest.city,
              nearest.name,
              nearest.lat,
              nearest.lon,
              nearest.lines,
            )
            setDepartures(deps?.slice(0, 4) ?? [])
          }
        } catch (e) {
          setError('Durak bilgisi alınamadı.')
        } finally {
          setLoading(false)
        }
      },
      () => {
        setLoading(false)
        setError('Konum izni alınamadı.')
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
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

  const firstByLine = new Map<string, StopDeparture>()
  if (departures) {
    for (const d of departures) {
      if (!firstByLine.has(d.line)) firstByLine.set(d.line, d)
    }
  }

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
          <p className="text-xs text-muted">{stop.city} · {formatDistance(stop.distance_m)}</p>
        </div>
        <span className="shrink-0 rounded-full bg-accent/10 px-2 py-1 text-xs font-bold text-accent">Detay</span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {Array.from(firstByLine.values()).map((d) => (
          <span
            key={d.line}
            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
              d.source === 'tahmini'
                ? 'bg-bg/60 italic text-muted'
                : 'bg-accent/15 text-accent'
            }`}
          >
            {d.line}
            <span className="tabular-nums">{timeText(d.minutes_ahead)}</span>
          </span>
        ))}
        {departures !== null && firstByLine.size === 0 && (
          <span className="text-xs text-muted">Yakında kalkış yok</span>
        )}
      </div>
    </button>
  )
}
