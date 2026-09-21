import { useState, type ReactElement } from 'react'
import {
  fetchVibeRoutes,
  type PlanResult,
  type VibeMood,
  type VibeResponse,
} from '@/lib/api'
import { getTier } from '@/lib/auth'
import UpgradeSheet from '@/components/UpgradeSheet'

const MOODS: { id: VibeMood; label: string; icon: string; hint: string }[] = [
  { id: 'sakin', label: 'Sakin', icon: '🌿', hint: 'Az yürüme, az aktarma' },
  { id: 'ekonomik', label: 'Ekonomik', icon: '💰', hint: 'En düşük maliyet' },
  { id: 'manzarali', label: 'Manzaralı', icon: '🌅', hint: 'Vapur ve sahil' },
  { id: 'kahve', label: 'Kahve Molalı', icon: '☕', hint: 'Mola noktalarıyla' },
]

const FREE_MOODS: VibeMood[] = ['sakin', 'ekonomik']

export default function VibeCard({
  plan,
  city,
}: {
  plan: PlanResult | null
  city: string
}): ReactElement {
  const [mood, setMood] = useState<VibeMood | null>(null)
  const [result, setResult] = useState<VibeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [upgradeOpen, setUpgradeOpen] = useState(false)

  const tier = getTier()

  async function apply(next: VibeMood) {
    if (!plan) {
      setError('Önce yukarıdan bir rota arayın, sonra mod seçin.')
      return
    }
    if (!FREE_MOODS.includes(next) && tier !== 'lite' && tier !== 'premium') {
      setUpgradeOpen(true)
      return
    }
    setMood(next)
    setLoading(true)
    setError(null)
    try {
      const res = await fetchVibeRoutes({
        start_lat: plan.start_coord.lat,
        start_lon: plan.start_coord.lon,
        end_lat: plan.end_coord.lat,
        end_lon: plan.end_coord.lon,
        city,
        people: 1,
        vehicle: plan.vehicle_selected,
        mood: next,
      })
      setResult(res)
    } catch (e) {
      const err = e as Error & { status?: number }
      if (err.status === 403) setUpgradeOpen(true)
      else setError(err.message || 'Mod uygulanamadı.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-4 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-sm font-bold">Moduna Göre Rota</p>
      <p className="mt-0.5 text-xs text-muted">Bugün nasıl bir rota istiyorsun?</p>

      <div className="mt-3 grid grid-cols-2 gap-2">
        {MOODS.map((m) => {
          const locked = !FREE_MOODS.includes(m.id) && tier !== 'lite' && tier !== 'premium'
          const active = mood === m.id
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => void apply(m.id)}
              disabled={loading}
              className={`relative rounded-xl border p-3 text-left transition-colors disabled:opacity-60 ${
                active ? 'border-accent bg-accent/10' : 'border-line hover:border-accent/50'
              }`}
            >
              <span className="text-xl" aria-hidden="true">{m.icon}</span>
              <span className="ml-1.5 text-sm font-bold">{m.label}</span>
              {locked && (
                <span className="absolute right-2 top-2 text-sm" aria-label="Kilitli">🔒</span>
              )}
              <span className="mt-0.5 block text-[11px] text-muted">{m.hint}</span>
            </button>
          )
        })}
      </div>

      {loading && <p className="mt-3 text-xs text-muted">Mod uygulanıyor…</p>}
      {error && (
        <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {result && !loading && (
        <div className="mt-3 rounded-xl border border-line/60 bg-bg/40 p-3">
          {result.notes.map((n, i) => (
            <p key={i} className="text-xs leading-relaxed text-fg/90">• {n}</p>
          ))}
          {result.pois.length > 0 && (
            <div className="mt-2 border-t border-line/60 pt-2">
              <p className="text-[11px] font-bold uppercase tracking-wide text-muted">Yakındaki noktalar</p>
              {result.pois.map((p, i) => (
                <p key={i} className="mt-1 text-xs">
                  📍 <strong>{p.name}</strong>
                  {p.detail ? <span className="text-muted"> — {p.detail}</span> : null}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {upgradeOpen && <UpgradeSheet onClose={() => setUpgradeOpen(false)} />}
    </div>
  )
}
