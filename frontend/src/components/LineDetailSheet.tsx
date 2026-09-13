import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchLineDetails,
  type LineDetails,
} from '@/lib/api'

function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`
  const km = meters / 1000
  return `${km.toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`
}

const TYPE_LABEL: Record<string, string> = {
  bus: '🚌 Otobüs',
  metro: '🚇 Metro',
  tram: '🚊 Tramvay',
  ferry: '🚢 Vapur',
  minibus: '🚐 Dolmuş',
  rail: '🚆 Raylı',
}

export default function LineDetailSheet({
  city,
  line,
  lat,
  lon,
  onClose,
}: {
  city: string
  line: string
  lat?: number
  lon?: number
  onClose: () => void
}): ReactElement {
  const [data, setData] = useState<LineDetails | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setData(null)
    setError(false)

    fetchLineDetails(city, line, lat, lon)
      .then((res) => {
        if (cancelled) return
        if (res) setData(res)
        else setError(true)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })

    return () => {
      cancelled = true
    }
  }, [city, line, lat, lon])

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-bg" role="dialog" aria-modal="true">
      <div className="flex items-start gap-3 border-b border-line px-4 py-4">
        <button
          type="button"
          onClick={onClose}
          aria-label="Geri"
          className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line text-muted transition-colors hover:border-accent hover:text-accent"
        >
          ←
        </button>
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-accent px-2.5 py-0.5 text-sm font-extrabold text-accent-ink">
              {line}
            </span>
            {data?.type && TYPE_LABEL[data.type.toLowerCase()] && (
              <span className="text-xs font-semibold text-muted">{TYPE_LABEL[data.type.toLowerCase()]}</span>
            )}
          </p>
          {data?.name && <p className="mt-1 break-words text-sm font-bold">{data.name}</p>}
          <p className="text-xs text-muted">
            {data ? `${data.city} · ${data.stop_count} durak` : `${city} · ${line} hattı`}
          </p>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4">
        {error && (
          <p className="rounded-xl border border-line bg-surface-2 px-4 py-3 text-sm text-muted">
            Hat bilgisi yüklenemedi. Bağlantını kontrol edip tekrar dene.
          </p>
        )}

        {!error && !data && (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded-xl bg-surface-2/70" />
            ))}
          </div>
        )}

        {data && (
          <>
            {data.next_departures.length > 0 && (
              <div className="mb-4 rounded-xl border border-accent/30 bg-accent/5 p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-muted">
                  {lat != null ? 'Sana en yakın duraktan sonraki kalkışlar' : 'Sonraki kalkışlar'}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {data.next_departures.map((d, i) => (
                    <span key={i} className="rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent tabular-nums">
                      {d.time}
                      {d.source === 'tahmini' && ' (tahmini)'}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
              {lat != null ? 'Hattın durakları — sana yakından uzağa' : 'Hattın durakları'}
            </p>
            <ol className="space-y-1.5">
              {data.stops.map((stop, i) => (
                <li
                  key={`${stop.name}-${i}`}
                  className="flex items-center gap-3 rounded-xl border border-line bg-surface-2/60 px-3 py-2.5"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent/10 text-[10px] font-bold text-accent">
                    {i + 1}
                  </span>
                  <p className="min-w-0 flex-1 break-words text-sm">{stop.name}</p>
                  {stop.distance_m != null && (
                    <span className="shrink-0 text-xs text-muted tabular-nums">
                      {formatDistance(stop.distance_m)}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </>
        )}
      </div>
    </div>
  )
}
