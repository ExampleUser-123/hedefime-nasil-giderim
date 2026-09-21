import { useEffect, useState, type ReactElement } from 'react'
import { loadTargets, removeTarget } from '@/lib/game'
import type { GameTarget } from '@/lib/api'
import { getStoredUser } from '@/lib/auth'

export default function TargetsSection({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}): ReactElement {
  const [targets, setTargets] = useState<GameTarget[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)

  async function refresh() {
    setTargets(await loadTargets())
  }

  useEffect(() => {
    void refresh()
  }, [])

  async function remove(id: string) {
    setBusyId(id)
    setTargets(await removeTarget(id))
    setBusyId(null)
  }

  if (targets.length === 0) return <></>

  return (
    <div className="mt-4 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-sm font-bold">🧭 Hedeflerim</p>
      <p className="mt-0.5 text-xs text-muted">
        {getStoredUser() ? 'Hesabına kayıtlı hedefler' : 'Cihazdaki hedefler (giriş yapınca hesaba taşınır)'}
      </p>
      <div className="mt-2 space-y-2">
        {targets.map((t) => (
          <div key={t.id} className="flex items-center gap-2 rounded-xl border border-line/60 bg-bg/40 px-3 py-2">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold">{t.name}</p>
              {(t.address || t.city) && (
                <p className="truncate text-[11px] text-muted">
                  {[t.address, t.city].filter(Boolean).join(' · ')}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => onOpenRoute({ from: '', to: t.name, people: 1, mode: 'tumu' })}
              className="shrink-0 rounded-lg bg-accent px-2.5 py-1.5 text-xs font-bold text-accent-ink"
            >
              Git
            </button>
            <button
              type="button"
              onClick={() => void remove(t.id)}
              disabled={busyId === t.id}
              aria-label="Hedefi sil"
              className="shrink-0 text-xs text-muted hover:text-red-300 disabled:opacity-40"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
