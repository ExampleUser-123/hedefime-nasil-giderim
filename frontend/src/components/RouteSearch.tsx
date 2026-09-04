import { useState } from 'react'
import { fetchPlan, reverseGeocode, type Mode, type PlanResult } from '@/lib/api'
import RouteResults from '@/components/RouteResults'
import {
  IconBus,
  IconCar,
  IconLocate,
  IconMetro,
  IconPin,
  IconSwap,
  IconUsers,
  IconWalk,
} from '@/icons'

const MODES = [
  { id: 'otobus', label: 'Otobüs', icon: IconBus },
  { id: 'metro', label: 'Metro', icon: IconMetro },
  { id: 'yuruyus', label: 'Yürüyüş', icon: IconWalk },
  { id: 'arac', label: 'Araç', icon: IconCar },
] as const

export default function RouteSearch({
  mode,
  onModeChange,
  plan,
  onPlanChange,
  selectedIndex,
  onSelectIndex,
}: {
  mode: Mode
  onModeChange: (mode: Mode) => void
  plan: PlanResult | null
  onPlanChange: (plan: PlanResult | null) => void
  selectedIndex: number
  onSelectIndex: (index: number) => void
}) {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [loading, setLoading] = useState(false)
  const [locating, setLocating] = useState(false)
  const [people, setPeople] = useState(1)
  const [error, setError] = useState<string | null>(null)

  function swap() {
    setFrom(to)
    setTo(from)
  }

  async function search() {
    if (!from.trim() || !to.trim() || loading) return

    setLoading(true)
    setError(null)

    try {
      const nextPlan = await fetchPlan(from.trim(), to.trim(), people)
      onPlanChange(nextPlan)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rota alınamadı.')
    } finally {
      setLoading(false)
    }
  }

  function detectLocation() {
    if (locating) return

    if (!('geolocation' in navigator)) {
      setError('Tarayıcın konum desteği sunmuyor.')
      return
    }

    setLocating(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const place = await reverseGeocode(
            position.coords.latitude,
            position.coords.longitude,
          )

          setFrom(place.display_name.split(',').slice(0, 2).join(','))
        } catch (e) {
          setError(
            e instanceof Error && e.message !== 'Sunucuya ulaşılamadı. Backend çalışıyor mu?'
              ? e.message
              : 'Konumun bulunamadı. Lütfen elle yaz.',
          )
        } finally {
          setLocating(false)
        }
      },
      () => {
        setLocating(false)
        setError('Konum izni alınamadı. Tarayıcı ayarlarından izin verip tekrar dene.')
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
  }

  return (
    <div>
      <div className="rounded-2xl border border-line bg-surface-2/90 p-4 backdrop-blur-sm">
        <div className="relative">
          <span className="absolute left-4 top-8 -bottom-8 w-px border-l border-dashed border-line" aria-hidden="true" />

          <label className="relative flex items-center gap-3 rounded-xl bg-bg/60 px-4 py-3">
            <IconPin className="h-5 w-5 shrink-0 text-accent" />
            <input
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              placeholder="Nereden"
              className="w-full bg-transparent pr-11 text-[17px] font-medium outline-none"
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                detectLocation()
              }}
              aria-label="Konumumu kullan"
              disabled={locating}
              className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-muted transition-colors hover:text-accent disabled:opacity-40"
            >
              {locating ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-muted/30 border-t-accent" aria-hidden="true" />
              ) : (
                <IconLocate className="h-4.5 w-4.5" />
              )}
            </button>
          </label>

          <label className="mt-3 flex items-center gap-3 rounded-xl bg-bg/60 px-4 py-3">
            <IconPin className="h-5 w-5 shrink-0 text-fg" />
            <input
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="Nereye"
              className="w-full bg-transparent text-[17px] font-medium outline-none"
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
          </label>

          <button
            type="button"
            onClick={swap}
            aria-label="Başlangıç ve hedefi değiştir"
            className="absolute right-3 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-surface text-muted transition-colors hover:border-accent hover:text-accent"
          >
            <IconSwap className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-4 gap-2" role="radiogroup" aria-label="Ulaşım türü">
          {MODES.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="radio"
              aria-checked={mode === id}
              onClick={() => onModeChange(id)}
              className={`flex min-h-[44px] flex-col items-center justify-center gap-1 rounded-xl border px-2 py-2.5 text-xs font-medium transition-colors sm:flex-row sm:gap-1.5 sm:text-sm ${
                mode === id
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-line bg-bg/40 text-muted hover:border-muted hover:text-fg'
              }`}
            >
              <Icon className="h-4.5 w-4.5" />
              <span>{label}</span>
            </button>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between rounded-xl bg-bg/60 px-3 py-2">
          <span className="flex items-center gap-2 text-sm text-muted">
            <IconUsers className="h-4 w-4" />
            Kişi sayısı
          </span>
          <div className="flex items-center gap-1" role="group" aria-label="Kişi sayısı seçimi">
            <button
              type="button"
              onClick={() => setPeople((current) => Math.max(1, current - 1))}
              disabled={people <= 1}
              aria-label="Kişi sayısını azalt"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-lg font-bold text-muted transition-colors hover:bg-surface hover:text-accent disabled:opacity-30 disabled:hover:text-muted"
            >
              −
            </button>
            <span className="min-w-8 text-center text-sm font-bold tabular-nums" aria-live="polite">
              {people}
            </span>
            <button
              type="button"
              onClick={() => setPeople((current) => Math.min(8, current + 1))}
              disabled={people >= 8}
              aria-label="Kişi sayısını artır"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-lg font-bold text-muted transition-colors hover:bg-surface hover:text-accent disabled:opacity-30 disabled:hover:text-muted"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={search}
        disabled={loading || !from.trim() || !to.trim()}
        className="mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-accent text-base font-bold text-accent-ink transition-transform hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent-ink/30 border-t-accent-ink" aria-hidden="true" />
            Rota aranıyor...
          </>
        ) : (
          'Rota Bul'
        )}
      </button>

      {error && (
        <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {plan && (
        <RouteResults
          mode={mode}
          result={plan}
          people={people}
          selectedIndex={selectedIndex}
          onSelectIndex={onSelectIndex}
        />
      )}
    </div>
  )
}
