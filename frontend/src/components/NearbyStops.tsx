import { useEffect, useState, type ReactElement } from 'react'
import { fetchNearbyStops, type NearbyStop } from '@/lib/api'
import { useCurrentPosition } from '@/lib/geolocation'
import StopDetailSheet from '@/components/StopDetailSheet'

// '350 m' / '1,2 km' biciminde mesafe metni
function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`

  const km = meters / 1000
  return `${km.toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`
}

function SkeletonStopCard() {
  return (
    <div className="rounded-2xl border border-line bg-surface-2 p-4">
      <div className="flex items-center gap-3">
        <span className="h-9 w-9 animate-pulse rounded-xl bg-muted/20" />
        <div className="flex-1 space-y-2">
          <div className="h-3.5 w-2/3 animate-pulse rounded bg-muted/20" />
          <div className="h-3 w-1/4 animate-pulse rounded bg-muted/20" />
        </div>
      </div>
      <div className="mt-3 flex gap-1.5">
        <span className="h-6 w-12 animate-pulse rounded-full bg-muted/20" />
        <span className="h-6 w-10 animate-pulse rounded-full bg-muted/20" />
        <span className="h-6 w-14 animate-pulse rounded-full bg-muted/20" />
      </div>
    </div>
  )
}

export default function NearbyStops({
  onPlanTo,
}: {
  onPlanTo?: (name: string) => void
}): ReactElement {
  const { coords, error, loading, refresh } = useCurrentPosition()
  const [stops, setStops] = useState<NearbyStop[] | null>(null)
  const [fetching, setFetching] = useState(false)
  const [fetchFailed, setFetchFailed] = useState(false)
  const [selected, setSelected] = useState<NearbyStop | null>(null)

  useEffect(() => {
    let alive = true

    if (!coords) return undefined

    setFetching(true)
    setFetchFailed(false)

    fetchNearbyStops(coords.lat, coords.lon, 8)
      .then((data) => {
        if (!alive) return

        setStops(data)
        setFetchFailed(data == null)
      })
      .catch(() => {
        if (alive) setFetchFailed(true)
      })
      .finally(() => {
        if (alive) setFetching(false)
      })

    return () => {
      alive = false
    }
  }, [coords])

  return (
    <section aria-label="Yakın duraklar" className="space-y-3">
      <div className="flex items-center justify-between px-1">
        <h2 className="text-sm font-bold">Yakın Duraklar</h2>
        <button
          type="button"
          onClick={refresh}
          aria-label="Konumu yenile"
          className="text-xs font-bold text-accent underline-offset-2 hover:underline"
        >
          Yenile
        </button>
      </div>

      {loading && (
        <>
          <SkeletonStopCard />
          <SkeletonStopCard />
        </>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-4 text-sm">
          <p className="text-amber-200">
            Konum alınamadı: {error} — yakındaki durakları görebilmek için konum izni gerekiyor.
          </p>
          <button
            type="button"
            onClick={refresh}
            className="mt-2 flex min-h-[40px] w-full items-center justify-center rounded-xl border border-line bg-surface-2 font-bold text-accent transition-colors hover:bg-accent/10"
          >
            Tekrar dene
          </button>
        </div>
      )}

      {!loading && !error && fetching && (
        <>
          <SkeletonStopCard />
          <SkeletonStopCard />
        </>
      )}

      {!loading && !error && !fetching && fetchFailed && (
        <div className="rounded-2xl border border-line bg-surface-2 px-4 py-4 text-sm text-muted">
          Yakındaki duraklar şu anda alınamadı.
          <button
            type="button"
            onClick={refresh}
            className="mt-2 block font-bold text-accent underline-offset-2 hover:underline"
          >
            Tekrar dene
          </button>
        </div>
      )}

      {!loading && !error && !fetching && stops !== null && stops.length === 0 && (
        <div className="rounded-2xl border border-line bg-surface-2 px-4 py-4 text-sm text-muted">
          Yakınında durak bulunamadı.
        </div>
      )}

      {!loading && !error && !fetching && stops !== null && stops.length > 0 && (
        <div className="space-y-3">
          {stops.map((stop) => (
            <button
              key={`${stop.city}|${stop.stop_id}`}
              type="button"
              onClick={() => setSelected(stop)}
              className="block w-full rounded-2xl border border-line bg-surface-2/90 p-4 text-left transition-colors hover:border-accent/60"
            >
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-accent">
                  <svg
                    viewBox="0 0 24 24"
                    className="h-4.5 w-4.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold">{stop.name}</p>
                  <p className="text-xs text-muted tabular-nums">{formatDistance(stop.distance_m)}</p>
                </div>
              </div>

              {stop.lines.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {stop.lines.slice(0, 6).map((line) => (
                    <span
                      key={line}
                      className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums"
                    >
                      {line}
                    </span>
                  ))}
                  {stop.lines.length > 6 && (
                    <span className="rounded-full bg-bg/60 px-2 py-0.5 text-xs text-muted">
                      +{stop.lines.length - 6}
                    </span>
                  )}
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {selected && (
        <StopDetailSheet
          stop={selected}
          onClose={() => setSelected(null)}
          onPlanTo={onPlanTo}
        />
      )}
    </section>
  )
}
