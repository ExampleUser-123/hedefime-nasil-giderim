import { useState } from 'react'
import { fetchPlan, type PlanResult } from '@/lib/api'
import {
  IconBus,
  IconCar,
  IconClock,
  IconMetro,
  IconPin,
  IconRoute,
  IconSwap,
  IconWallet,
  IconWalk,
} from '@/icons'

const MODES = [
  { id: 'otobus', label: 'Otobüs', icon: IconBus },
  { id: 'metro', label: 'Metro', icon: IconMetro },
  { id: 'yuruyus', label: 'Yürüyüş', icon: IconWalk },
  { id: 'arac', label: 'Araç', icon: IconCar },
] as const

type Mode = (typeof MODES)[number]['id']

export default function RouteSearch() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [mode, setMode] = useState<Mode>('otobus')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PlanResult | null>(null)

  function swap() {
    setFrom(to)
    setTo(from)
  }

  async function search() {
    if (!from.trim() || !to.trim() || loading) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const plan = await fetchPlan(from.trim(), to.trim())
      setResult(plan)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rota alınamadı.')
    } finally {
      setLoading(false)
    }
  }

  const fastest = result?.public_transport.recommendations.fastest ?? null

  return (
    <div>
      <div className="rounded-2xl border border-line bg-surface-2/90 p-4 backdrop-blur-sm">
        <div className="relative">
          <span className="absolute left-4 top-8 -bottom-8 w-px border-l border-dashed border-line" aria-hidden="true" />

          <label className="flex items-center gap-3 rounded-xl bg-bg/60 px-4 py-3">
            <IconPin className="h-5 w-5 shrink-0 text-accent" />
            <input
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              placeholder="Nereden"
              className="w-full bg-transparent text-[17px] font-medium outline-none"
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
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
              onClick={() => setMode(id)}
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

      {result && (
        <div className="mt-4 space-y-3 rounded-2xl border border-line bg-surface-2/90 p-4">
          {result.car && (
            <div className="flex items-start gap-3">
              <IconCar className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
              <div className="min-w-0">
                <p className="text-sm font-semibold">Arabayla</p>
                <p className="mt-0.5 text-sm text-muted">
                  {result.car.duration_minutes} dk · {result.car.distance_km} km ·{' '}
                  {result.car.total_cost} TL yakıt
                </p>
              </div>
            </div>
          )}

          {fastest && (
            <div className="flex items-start gap-3 border-t border-line pt-3">
              <IconBus className="mt-0.5 h-5 w-5 shrink-0 text-accent" />
              <div className="min-w-0">
                <p className="text-sm font-semibold">Toplu taşımada en hızlı</p>
                <p className="mt-0.5 text-sm text-muted">
                  {fastest.duration_minutes ?? '?'} dk
                  {fastest.fee != null && ` · ${fastest.fee} TL`}
                  {fastest.departure_time && ` · kalkış ${fastest.departure_time}`}
                </p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 border-t border-line pt-3 text-xs text-muted">
            <IconRoute className="h-4 w-4" />
            <span className="truncate">{result.start}</span>
            <span aria-hidden="true">→</span>
            <span className="truncate">{result.destination}</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-muted">
            <IconClock className="h-3.5 w-3.5" />
            <span>Bilgiler anlık olarak hesaplandı</span>
            <IconWallet className="ml-auto h-3.5 w-3.5" />
          </div>
        </div>
      )}
    </div>
  )
}
