import { useEffect, useRef, useState, type ReactElement } from 'react'
import { fetchStopDepartures, type NearbyStop, type StopDeparture } from '@/lib/api'
import {
  addReminder,
  cancelReminder,
  isReminderActive,
  type AddReminderResult,
} from '@/lib/reminders'

const LEAD_OPTIONS = [5, 10, 15] as const
const LEAD_STORAGE_KEY = 'hatirlatic_lead_v1'

// '350 m' / '1,2 km' biciminde mesafe metni
function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`

  const km = meters / 1000
  return `${km.toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`
}

// DepartureBadge'in estetigine uyan mini sefer rozeti (bilesen yeniden kullanilmaz).
function MiniDepartureBadge({ departure }: { departure: StopDeparture }): ReactElement {
  if (departure.source === 'tahmini') {
    return (
      <span
        className="rounded-full bg-bg/60 px-2 py-0.5 text-xs italic text-muted tabular-nums"
        title={`Tahmini kalkış: ${departure.time}`}
      >
        ~{departure.minutes_ahead} dk (tahmini)
      </span>
    )
  }

  return (
    <span
      className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums"
      title={`Kalkış saati: ${departure.time}`}
    >
      ⏱ {departure.minutes_ahead} dk
    </span>
  )
}

function DepartureSkeleton() {
  return <span className="h-5 w-16 animate-pulse rounded-full bg-muted/20" />
}

export default function StopDetailSheet({
  stop,
  onClose,
  onPlanTo,
}: {
  stop: NearbyStop
  onClose: () => void
  onPlanTo?: (name: string) => void
}): ReactElement {
  const [departures, setDepartures] = useState<StopDeparture[] | null>(null)
  const [failed, setFailed] = useState(false)
  const aliveRef = useRef(true)
  const [leadMin, setLeadMin] = useState<number>(() => {
    try {
      const raw = localStorage.getItem(LEAD_STORAGE_KEY)
      return raw ? Number.parseInt(raw, 10) : 10
    } catch {
      return 10
    }
  })
  const [activeIds, setActiveIds] = useState<Set<string>>(new Set())
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    aliveRef.current = true

    fetchStopDepartures(stop.city, stop.name, stop.lat, stop.lon, stop.lines)
      .then((data) => {
        if (aliveRef.current) setDepartures(data ?? null)
      })
      .catch(() => {
        if (aliveRef.current) setFailed(true)
      })

    return () => {
      aliveRef.current = false
    }
  }, [stop])

  // Her hat icin bir sonraki sefer (null ise rozet yok)
  const nextByLine = new Map<string, StopDeparture | null>()

  if (departures) {
    for (const line of stop.lines) {
      const first = departures.find((d) => d.line === line) ?? null
      nextByLine.set(line, first)
    }
  }

  // Acilista mevcut hatirlaticlari isaretle
  useEffect(() => {
    if (!departures) return

    const active = new Set<string>()

    for (const d of departures) {
      if (isReminderActive(stop.name, stop.city, d.line, d.time)) {
        active.add(`${d.line}|${d.time}`)
      }
    }
    setActiveIds(active)
  }, [departures, stop])

  function pickLead(min: number): void {
    setLeadMin(min)
    try {
      localStorage.setItem(LEAD_STORAGE_KEY, String(min))
    } catch {
      // tercihi saklayamazsak sadece oturumluk kalir
    }
  }

  async function handleToggleReminder(dep: StopDeparture): Promise<void> {
    setNotice(null)
    const key = `${dep.line}|${dep.time}`

    if (activeIds.has(key)) {
      await cancelReminder(stop.name, stop.city, dep.line, dep.time)
      setActiveIds((prev) => {
        const next = new Set(prev)
        next.delete(key)
        return next
      })
      return
    }

    const result: AddReminderResult = await addReminder({
      stopName: stop.name,
      city: stop.city,
      line: dep.line,
      time: dep.time,
      leadMin,
    })

    if (result.ok) {
      setActiveIds((prev) => new Set(prev).add(key))
      return
    }

    if (result.reason === 'too-late') {
      setNotice('Sefer çok yakın, uyarı kurulamadı.')
    } else if (result.reason === 'permission') {
      setNotice('Bildirim izni verilmedi. Ayarlardan izin verip tekrar dene.')
    } else {
      setNotice('Hatırlatic kurulamadı, tekrar dene.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={`${stop.name} durak detayı`}
    >
      <div className="absolute inset-0 bg-bg/70 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative flex max-h-[80vh] w-full flex-col overflow-hidden rounded-t-3xl border border-line bg-surface sm:max-w-lg">
        <header className="flex items-start gap-3 border-b border-line px-5 py-4">
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
            <p className="text-xs text-muted tabular-nums">
              {stop.city} · {formatDistance(stop.distance_m)}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Durak detayını kapat"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </header>

        <div className="flex-1 space-y-2.5 overflow-y-auto px-5 py-4">
          {!failed && departures !== null && (
            <div className="flex items-center justify-between px-1">
              <p className="text-xs font-bold uppercase tracking-wide text-muted">Sefer uyarısı</p>
              <div className="flex items-center gap-1">
                {LEAD_OPTIONS.map((min) => (
                  <button
                    key={min}
                    type="button"
                    onClick={() => pickLead(min)}
                    aria-pressed={leadMin === min}
                    className={`rounded-full px-2.5 py-1 text-xs font-bold transition-colors ${
                      leadMin === min
                        ? 'bg-accent text-accent-ink'
                        : 'bg-surface-2 text-muted hover:text-fg'
                    }`}
                  >
                    {min} dk
                  </button>
                ))}
              </div>
            </div>
          )}

          {!failed && departures === null && (
            <>
              {stop.lines.slice(0, 5).map((line) => (
                <div key={line} className="flex items-center justify-between rounded-2xl border border-line bg-surface-2 px-4 py-3">
                  <span className="h-6 w-14 animate-pulse rounded-full bg-muted/20" />
                  <DepartureSkeleton />
                </div>
              ))}
            </>
          )}

          {!failed && departures !== null && (
            <>
              {stop.lines.map((line) => {
                const next = nextByLine.get(line)

                return (
                  <div
                    key={line}
                    className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-surface-2 px-4 py-3"
                  >
                    <span className="rounded-full bg-accent/15 px-2.5 py-0.5 text-sm font-bold text-accent tabular-nums">
                      {line}
                    </span>
                    {next ? (
                      <div className="flex items-center gap-2">
                        <MiniDepartureBadge departure={next} />
                        <button
                          type="button"
                          onClick={() => handleToggleReminder(next)}
                          aria-label={`${line} hattı ${next.time} seferi için hatırlatıcı`}
                          aria-pressed={activeIds.has(`${next.line}|${next.time}`)}
                          className={`flex h-8 w-8 items-center justify-center rounded-full border transition-colors ${
                            activeIds.has(`${next.line}|${next.time}`)
                              ? 'border-accent bg-accent/15 text-accent'
                              : 'border-line text-muted hover:border-accent hover:text-accent'
                          }`}
                        >
                          {activeIds.has(`${next.line}|${next.time}`) ? '🔔' : '🔕'}
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-muted">Bugün sefer yok</span>
                    )}
                  </div>
                )
              })}
            </>
          )}

          {failed && (
            <p role="alert" className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              Sefer bilgisi şu anda alınamadı. Durak yine de yakın duraklar listesinde.
            </p>
          )}

          {notice && (
            <p role="alert" className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              {notice}
            </p>
          )}
        </div>

        {onPlanTo && (
          <footer className="border-t border-line p-4">
            <button
              type="button"
              onClick={() => onPlanTo(stop.name)}
              className="flex min-h-[46px] w-full items-center justify-center rounded-xl bg-accent font-bold text-accent-ink transition-opacity hover:opacity-90"
            >
              Buraya rota
            </button>
          </footer>
        )}
      </div>
    </div>
  )
}
