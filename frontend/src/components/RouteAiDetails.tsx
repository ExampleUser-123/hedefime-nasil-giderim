import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchRouteDetails,
  type RouteDetailResponse,
  type TransitLeg,
  type TransitRoute,
} from '@/lib/api'

const VERB: Record<string, string> = {
  WALK: '🚶 YÜRÜ',
  TRAIN: '🚆 BİN',
  METRO: '🚇 BİN',
  BUS: '🚌 BİN',
  TRAM: '🚊 BİN',
  FERRY: '⛴ BİN',
}

function StepCard({ step, index }: { step: RouteDetailResponse['steps'][number]; index: number }) {
  return (
    <li className="flex items-start gap-2 py-2">
      <span
        className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 px-1 text-[10px] font-bold text-accent tabular-nums"
        aria-label={`${index + 1}. adım`}
      >
        {index + 1}
      </span>
      <div className="min-w-0 flex-1">
        <p>
          <span className="mr-1.5 rounded-md bg-accent/15 px-1.5 py-0.5 text-[10px] font-extrabold tracking-wide text-accent">
            {VERB[step.step_type] ?? '➡ ADIM'}
          </span>
          <span className="break-words text-sm">{step.instruction}</span>
        </p>

        <div className="mt-1 space-y-0.5 text-xs">
          {step.line_name && (
            <p className="break-words font-semibold">Hat: {step.line_name}</p>
          )}
          {step.departure_stop && (
            <p className="break-words">
              <span className="font-bold text-accent">📍 Biniş: </span>
              {step.departure_stop}
            </p>
          )}
          {step.arrival_stop && (
            <p className="break-words">
              <span className="font-bold text-accent">📍 İniş: </span>
              {step.arrival_stop}
            </p>
          )}
          {step.departure_times && step.departure_times.length > 0 ? (
            <p className="tabular-nums">
              🕒 Seferler: {step.departure_times.join(', ')}
            </p>
          ) : (
            step.step_type !== 'WALK' && (
              <p className="text-muted">Sefer saati veride yok</p>
            )
          )}
          {step.duration && (
            <p className="text-muted tabular-nums">⏱ Süre: {step.duration}</p>
          )}
          {step.direction && (
            <p className="break-words text-muted">Yön: {step.direction}</p>
          )}
        </div>
      </div>
    </li>
  )
}

/**
 * Secili rotanin AI destekli adim adim detayi.
 * Adimlar backend'in gercek leg verisinden kurulur; Gemini yalnizca ozeti yazar.
 */
export default function RouteAiDetails({
  from,
  to,
  city,
  startLat,
  startLon,
  people,
  route,
  onRequireLogin,
}: {
  from: string
  to: string
  city: string
  startLat?: number
  startLon?: number
  people: number
  route: TransitRoute
  onRequireLogin: () => void
}): ReactElement {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<RouteDetailResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Rota degisince eski detay gecersiz
  const legKey = route.legs
    .map((leg: TransitLeg) => [leg.type, leg.line, leg.from_stop, leg.to_stop].join('|'))
    .join('>')
  useEffect(() => {
    setOpen(false)
    setData(null)
    setError(null)
  }, [legKey])

  async function load() {
    if (open) {
      setOpen(false)
      return
    }
    setOpen(true)
    if (data) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetchRouteDetails({
        from,
        to,
        city,
        start_lat: startLat,
        start_lon: startLon,
        people,
        total_minutes: route.duration_minutes,
        fee: route.fee,
        legs: route.legs,
      })
      setData(res)
    } catch (e) {
      if (e instanceof Error && (e as Error & { status?: number }).status === 401) {
        setOpen(false)
        onRequireLogin()
        return
      }
      setError(e instanceof Error ? e.message : 'Detay alınamadı.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-2xl border border-accent/30 bg-accent/5 p-4">
      <button
        type="button"
        onClick={() => void load()}
        aria-expanded={open}
        className="flex min-h-[44px] w-full items-center justify-center gap-1.5 rounded-xl bg-accent text-sm font-extrabold text-accent-ink transition-opacity hover:opacity-90 disabled:opacity-50"
        disabled={loading}
      >
        {loading ? '✨ AI detayı hazırlanıyor…' : open ? 'AI Detayını gizle ↑' : '✨ Detayı Göster — Adım Adım'}
      </button>

      {error && (
        <p role="alert" className="mt-2 text-xs text-red-300">{error}</p>
      )}

      {open && data && (
        <div className="mt-3">
          {data.summary_text && (
            <p className="rounded-xl bg-bg/60 px-3 py-2.5 text-xs leading-relaxed">
              ✨ {data.summary_text}
            </p>
          )}

          <ol className="mt-1 divide-y divide-line/60">
            {data.steps.map((step, i) => (
              <StepCard key={i} step={step} index={i} />
            ))}
          </ol>

          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div className="rounded-xl border border-line px-3 py-2">
              <p className="text-xs text-muted">Toplam süre</p>
              <p className="font-bold tabular-nums">{data.total_duration}</p>
            </div>
            <div className="rounded-xl border border-line px-3 py-2">
              <p className="text-xs text-muted">Toplam ücret</p>
              <p className="font-bold tabular-nums">{data.total_price}</p>
            </div>
            <div className="rounded-xl border border-line px-3 py-2">
              <p className="text-xs text-muted">Yürüme</p>
              <p className="font-bold tabular-nums">
                {data.total_walking_m >= 1000
                  ? `${(data.total_walking_m / 1000).toFixed(1).replace('.', ',')} km`
                  : `${data.total_walking_m} m`}
              </p>
            </div>
            <div className="rounded-xl border border-line px-3 py-2">
              <p className="text-xs text-muted">Aktarma</p>
              <p className="font-bold tabular-nums">{data.transfer_count}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
