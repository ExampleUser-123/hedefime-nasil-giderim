import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchMagicUsage,
  resolveMagicShare,
  type MagicResult,
} from '@/lib/api'
import { getStoredUser } from '@/lib/auth'
import { saveTarget } from '@/lib/game'
import { consumePendingShare } from '@/lib/shareIntent'
import UpgradeSheet from '@/components/UpgradeSheet'

export default function MagicShare({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}): ReactElement {
  const [text, setText] = useState('')
  const [result, setResult] = useState<MagicResult | null>(null)
  const [editName, setEditName] = useState('')
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [quota, setQuota] = useState<{ used: number; limit: number } | null>(null)
  const [upgradeOpen, setUpgradeOpen] = useState(false)
  const [saved, setSaved] = useState(false)

  const loggedIn = !!getStoredUser()

  async function refreshQuota() {
    if (!loggedIn) return
    try {
      const u = await fetchMagicUsage()
      setQuota({ used: u.used, limit: u.limit })
    } catch {
      // sessizce gec
    }
  }

  useEffect(() => {
    void refreshQuota()
    // Native paylasimdan gelen metin varsa kutuya koyup otomatik coz
    const pending = consumePendingShare()
    if (pending) {
      setText(pending)
      void resolve(pending)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function resolve(override?: string) {
    const value = (override ?? text).trim()
    if (!value || loading) return
    if (!loggedIn) {
      setError('Magic Share için giriş yapmalısınız.')
      return
    }
    setLoading(true)
    setError(null)
    setSaved(false)
    try {
      const res = await resolveMagicShare(value)
      setResult(res)
      setEditName(res.name)
      setEditing(false)
      setQuota(res.usage ?? null)
    } catch (e) {
      const err = e as Error & { status?: number }
      if (err.status === 429) {
        setError('Günlük Magic Share hakkın doldu. Bu özelliği sınırsız kullanmak için Lite veya Premium\u2019a geç.')
        setUpgradeOpen(true)
      } else {
        setError(err.message || 'Magic Share işlemi başarısız oldu. Lütfen tekrar deneyin.')
      }
    } finally {
      setLoading(false)
    }
  }

  async function addToTargets() {
    if (!result) return
    const name = (editing ? editName : result.name).trim() || result.name
    await saveTarget({
      name,
      lat: result.lat,
      lon: result.lon,
      address: result.address,
      city: result.city,
    })
    setSaved(true)
  }

  return (
    <div className="mt-4 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-sm font-bold">📍 Beni Buraya Götür</p>
      <p className="mt-0.5 text-xs text-muted">
        Harita linkini yapıştır, konumu algılayalım.
        {quota && quota.limit >= 0 && (
          <span> Bugünkü hakkın: {Math.max(0, quota.limit - quota.used)}/{quota.limit}</span>
        )}
      </p>

      <div className="mt-3 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Google Maps / Apple Maps linki veya adres"
          className="min-h-[44px] flex-1 rounded-xl border border-line bg-bg px-3 text-sm outline-none transition-colors focus:border-accent"
        />
        <button
          type="button"
          onClick={() => void resolve()}
          disabled={loading || !text.trim()}
          className="shrink-0 rounded-xl bg-accent px-4 text-sm font-bold text-accent-ink disabled:opacity-50"
        >
          {loading ? '…' : 'Bul'}
        </button>
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {result && !loading && (
        <div className="mt-3 rounded-xl border border-line/60 bg-bg/40 p-3">
          {editing ? (
            <input
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              maxLength={80}
              className="w-full rounded-lg border border-line bg-bg px-2 py-1.5 text-sm font-bold outline-none focus:border-accent"
            />
          ) : (
            <p className="text-sm font-bold">
              Burası {result.name} olarak algılandı.
            </p>
          )}
          <p className="mt-1 truncate text-xs text-muted">
            {[result.address, result.city].filter(Boolean).join(' · ')}
          </p>
          {result.confidence === 'medium' && (
            <p className="mt-1 text-[11px] text-amber-300/90">
              Eşleşme kesin değil — yanlışsa düzenleyin.
            </p>
          )}

          <div className="mt-2.5 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void addToTargets()}
              disabled={saved}
              className="rounded-lg border border-line px-3 py-1.5 text-xs font-bold text-accent disabled:opacity-50"
            >
              {saved ? '✓ Hedeflerde' : 'Hedefime Ekle'}
            </button>
            <button
              type="button"
              onClick={() => onOpenRoute({ from: '', to: result.name, people: 1, mode: 'tumu' })}
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-bold text-accent-ink"
            >
              Buraya Git
            </button>
            <button
              type="button"
              onClick={() => {
                setEditName(result.name)
                setEditing((v) => !v)
              }}
              className="rounded-lg border border-line px-3 py-1.5 text-xs text-muted"
            >
              {editing ? 'Vazgeç' : 'Eşleşmeyi Düzenle'}
            </button>
          </div>
        </div>
      )}

      {upgradeOpen && <UpgradeSheet onClose={() => setUpgradeOpen(false)} />}
    </div>
  )
}
