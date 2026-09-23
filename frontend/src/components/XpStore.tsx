import { useEffect, useState, type ReactElement } from 'react'
import { fetchXpStore, redeemXpStore, type XpStoreItem } from '@/lib/api'
import { getStoredUser } from '@/lib/auth'

/** Profil ici XP Magazasi: bakiye + urunler + tek tikla takas. */
export default function XpStore(): ReactElement {
  const [xp, setXp] = useState<number | null>(null)
  const [items, setItems] = useState<XpStoreItem[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    if (!getStoredUser()) return
    try {
      const data = await fetchXpStore()
      setXp(data.xp)
      setItems(data.items)
    } catch {
      // sessizce gec
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  async function redeem(id: string) {
    if (busyId) return
    setBusyId(id)
    setMessage(null)
    setError(null)
    try {
      const res = await redeemXpStore(id)
      if (!res) throw new Error('İşlem başarısız oldu. Lütfen tekrar deneyin.')
      setMessage(res.effect)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'İşlem başarısız oldu.')
    } finally {
      setBusyId(null)
    }
  }

  if (!getStoredUser()) return <></>

  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-muted">🎁 XP Mağazası</p>
        {xp !== null && (
          <p className="rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent tabular-nums">
            {xp} XP
          </p>
        )}
      </div>

      <div className="mt-2 space-y-2">
        {items.map((item) => {
          // unlimited_day yeniden alinabilir (sure uzar); diger sahipli urunler kilitli
          const repurchasable = item.id === 'unlimited_day' || item.id === 'magic_plus3' || item.id === 'ai_plus5'
          const locked = item.owned && !repurchasable
          const label = busyId === item.id
            ? '…'
            : item.owned && item.id === 'unlimited_day'
              ? 'Süreyi Uzat'
              : item.owned && !repurchasable
                ? 'Aktif ✓'
                : 'Takas Et'
          return (
          <div key={item.id} className="flex items-center gap-2 rounded-xl border border-line/60 bg-bg/40 px-3 py-2">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold">{item.name}</p>
              <p className="text-[11px] text-muted">{item.desc}</p>
              <p className="mt-0.5 text-[11px] font-bold text-accent tabular-nums">{item.cost} XP</p>
            </div>
            <button
              type="button"
              onClick={() => void redeem(item.id)}
              disabled={busyId !== null || locked || (xp !== null && xp < item.cost)}
              className="shrink-0 rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-accent-ink disabled:opacity-40"
            >
              {label}
            </button>
          </div>
          )
        })}
      </div>

      {message && (
        <p role="status" className="mt-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          {message}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  )
}
