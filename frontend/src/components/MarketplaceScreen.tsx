import { useEffect, useState, type ReactElement } from 'react'
import {
  commentMarketplace,
  deleteMarketplace,
  fetchMarketplace,
  publishMarketplace,
  rateMarketplace,
  type CommunityRoute,
} from '@/lib/api'
import { getStoredUser } from '@/lib/auth'

export default function MarketplaceScreen({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}): ReactElement {
  const [routes, setRoutes] = useState<CommunityRoute[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [sort, setSort] = useState<'new' | 'top'>('new')
  const [commentFor, setCommentFor] = useState<string | null>(null)
  const [commentText, setCommentText] = useState('')

  const loggedIn = !!getStoredUser()
  const myId = getStoredUser()?.id

  async function refresh(activeSort: 'new' | 'top' = sort) {
    setLoading(true)
    setRoutes(await fetchMarketplace(20, 0, activeSort))
    setLoading(false)
  }

  useEffect(() => {
    void refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function switchSort(next: 'new' | 'top') {
    setSort(next)
    void refresh(next)
  }

  async function publish() {
    if (!title.trim() || busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await publishMarketplace({
        title: title.trim(),
        description: description.trim(),
        from: from.trim(),
        to: to.trim(),
      })
      if (!res) throw new Error('Paylaşım başarısız oldu. Lütfen tekrar deneyin.')
      setTitle('')
      setDescription('')
      setFrom('')
      setTo('')
      setFormOpen(false)
      setInfo(`Paylaşıldı! +30 XP kazandın.`)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Paylaşım başarısız oldu.')
    } finally {
      setBusy(false)
    }
  }

  async function remove(id: string) {
    await deleteMarketplace(id)
    await refresh()
  }

  async function rate(id: string, stars: number) {
    if (!loggedIn) {
      setError('Puan vermek için giriş yapmalısınız.')
      return
    }
    const res = await rateMarketplace(id, stars)
    if (!res) {
      setError('Puan kaydedilemedi. Lütfen tekrar deneyin.')
      return
    }
    setRoutes((prev) => prev.map((r) => (r.id === id ? res.route : r)))
    if (res.profile?.new_badges?.length) {
      setInfo(`+10 XP! Yeni rozet: ${res.profile.new_badges.map((b) => b.name).join(', ')}`)
    }
  }

  async function sendComment(id: string) {
    const text = commentText.trim()
    if (!text || !loggedIn) return
    const res = await commentMarketplace(id, text)
    if (!res) {
      setError('Yorum kaydedilemedi. Lütfen tekrar deneyin.')
      return
    }
    setRoutes((prev) => prev.map((r) => (r.id === id ? res.route : r)))
    setCommentText('')
    setCommentFor(null)
    if (res.profile?.new_badges?.length) {
      setInfo(`+10 XP! Yeni rozet: ${res.profile.new_badges.map((b) => b.name).join(', ')}`)
    }
  }

  return (
    <div className="relative z-10 mx-auto w-full max-w-xl px-4 pb-28 pt-6 sm:px-6">
      <div className="flex items-center gap-2.5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 text-xl" aria-hidden="true">🧭</span>
        <div>
          <h1 className="text-xl font-bold">Keşfet</h1>
          <p className="text-xs text-muted">Topluluğun paylaştığı rota ve mekanlar</p>
        </div>
      </div>

      <div className="mt-5">
        {loggedIn && (
          <button
            type="button"
            onClick={() => setFormOpen((v) => !v)}
            className="w-full rounded-2xl bg-accent py-3 text-sm font-bold text-accent-ink"
          >
            {formOpen ? 'Vazgeç' : '+ Rotanı Paylaş (+30 XP)'}
          </button>
        )}

        {formOpen && (
          <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={80}
              placeholder="Başlık (örn. Boğaz'da gün batımı turu)"
              className="w-full rounded-xl border border-line bg-bg px-3 py-2.5 text-sm outline-none focus:border-accent"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              rows={2}
              placeholder="Açıklama (isteğe bağlı)"
              className="mt-2 w-full rounded-xl border border-line bg-bg px-3 py-2.5 text-sm outline-none focus:border-accent"
            />
            <div className="mt-2 grid grid-cols-2 gap-2">
              <input
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                maxLength={160}
                placeholder="Nereden"
                className="rounded-xl border border-line bg-bg px-3 py-2.5 text-sm outline-none focus:border-accent"
              />
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                maxLength={160}
                placeholder="Nereye"
                className="rounded-xl border border-line bg-bg px-3 py-2.5 text-sm outline-none focus:border-accent"
              />
            </div>
            <button
              type="button"
              onClick={() => void publish()}
              disabled={busy || !title.trim()}
              className="mt-3 w-full rounded-xl bg-accent py-2.5 text-sm font-bold text-accent-ink disabled:opacity-50"
            >
              {busy ? 'Paylaşılıyor…' : 'Toplulukla Paylaş'}
            </button>
          </div>
        )}

        {error && (
          <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {error}
          </p>
        )}
        {info && (
          <p role="status" className="mt-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
            {info}
          </p>
        )}

        <div className="mt-4 space-y-3">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => switchSort('new')}
              className={`flex-1 rounded-xl border py-2 text-xs font-bold ${sort === 'new' ? 'border-accent bg-accent/10 text-accent' : 'border-line text-muted'}`}
            >
              🆕 En Yeniler
            </button>
            <button
              type="button"
              onClick={() => switchSort('top')}
              className={`flex-1 rounded-xl border py-2 text-xs font-bold ${sort === 'top' ? 'border-accent bg-accent/10 text-accent' : 'border-line text-muted'}`}
            >
              ⭐ En Çok Beğenilenler
            </button>
          </div>
          {loading && <p className="text-sm text-muted">Yükleniyor…</p>}
          {!loading && routes.length === 0 && (
            <p className="rounded-2xl border border-line bg-surface-2/90 px-4 py-6 text-center text-sm text-muted">
              Henüz paylaşım yok — ilk paylaşan sen ol!
            </p>
          )}
          {routes.map((r) => (
            <article key={r.id} className="rounded-2xl border border-line bg-surface-2/90 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-bold">{r.title}</h2>
                  <p className="text-[11px] text-muted">
                    {r.user_name}{r.place?.city ? ` · ${r.place.city}` : ''}
                  </p>
                </div>
                {myId && r.user_id === myId && (
                  <button
                    type="button"
                    onClick={() => void remove(r.id)}
                    className="shrink-0 text-xs text-muted hover:text-red-300"
                    aria-label="Paylaşımı sil"
                  >
                    ✕
                  </button>
                )}
              </div>
              {r.description && (
                <p className="mt-1.5 text-xs leading-relaxed text-fg/85">{r.description}</p>
              )}
              {(r.from || r.to) && (
                <p className="mt-1.5 text-xs text-muted">
                  {r.from || '?'} → {r.to || '?'}
                </p>
              )}
              {r.place?.name && (
                <p className="mt-1 text-xs">📍 {r.place.name}</p>
              )}

              <div className="mt-2 flex items-center justify-between gap-2 border-t border-line/60 pt-2">
                <div className="flex items-center gap-1" role="group" aria-label="Puan ver">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => void rate(r.id, s)}
                      aria-label={`${s} yıldız ver`}
                      className="text-base leading-none text-amber-300/90 transition-transform hover:scale-125"
                    >
                      ★
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-muted tabular-nums">
                  {(r.rating_avg ?? 0) > 0 ? `★ ${r.rating_avg!.toFixed(1)}` : 'Puan yok'}
                  {(r.rating_count ?? 0) > 0 && ` (${r.rating_count} oy)`}
                  {(r.comment_count ?? 0) > 0 && ` · 💬 ${r.comment_count}`}
                </p>
              </div>

              {(r.comments ?? []).length > 0 && (
                <div className="mt-2 space-y-1.5 border-t border-line/60 pt-2">
                  {(r.comments ?? []).slice(-3).map((c, i) => (
                    <p key={i} className="text-[11px] leading-relaxed">
                      <strong>{c.user_name}:</strong>{' '}
                      <span className="text-fg/85">{c.text}</span>
                    </p>
                  ))}
                </div>
              )}

              {loggedIn && (
                commentFor === r.id ? (
                  <div className="mt-2 flex gap-2">
                    <input
                      value={commentText}
                      onChange={(e) => setCommentText(e.target.value)}
                      maxLength={300}
                      placeholder="Yorumun…"
                      className="min-h-[38px] flex-1 rounded-lg border border-line bg-bg px-2.5 text-xs outline-none focus:border-accent"
                    />
                    <button
                      type="button"
                      onClick={() => void sendComment(r.id)}
                      disabled={!commentText.trim()}
                      className="shrink-0 rounded-lg bg-accent px-3 text-xs font-bold text-accent-ink disabled:opacity-50"
                    >
                      Gönder
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setCommentFor(r.id)
                      setCommentText('')
                    }}
                    className="mt-2 text-[11px] font-semibold text-accent hover:underline"
                  >
                    💬 Yorum yaz
                  </button>
                )
              )}
              <button
                type="button"
                onClick={() => onOpenRoute({ from: r.from || '', to: r.to || r.place?.name || r.title, people: 1, mode: r.mode || 'tumu' })}
                className="mt-2.5 w-full rounded-xl border border-accent/40 py-2 text-xs font-bold text-accent"
              >
                Bu Rotayı Aç
              </button>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
