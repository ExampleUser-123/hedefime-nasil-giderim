import { useCallback, useEffect, useState, type ReactElement } from 'react'
import { getHistory, getSaved, type SavedRoute } from '@/lib/storage'

type RouteEntry = Pick<SavedRoute, 'from' | 'to'> & Partial<Pick<SavedRoute, 'people' | 'mode'>>

/** Baglanti koptugunda son rotalari ve favorileri gosteren cevrimdisi karti. */
export default function OfflineBanner({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}): ReactElement | null {
  const [offline, setOffline] = useState<boolean>(
    () => typeof navigator !== 'undefined' && navigator.onLine === false,
  )
  const [recent, setRecent] = useState<RouteEntry[]>([])
  const [favorites, setFavorites] = useState<RouteEntry[]>([])

  const refreshLists = useCallback(() => {
    try {
      setRecent(getHistory().slice(0, 5))
    } catch {
      setRecent([])
    }
    try {
      setFavorites(getSaved().slice(0, 5))
    } catch {
      setFavorites([])
    }
  }, [])

  useEffect(() => {
    const goOffline = () => {
      refreshLists()
      setOffline(true)
    }
    const goOnline = () => setOffline(false)
    window.addEventListener('offline', goOffline)
    window.addEventListener('online', goOnline)
    return () => {
      window.removeEventListener('offline', goOffline)
      window.removeEventListener('online', goOnline)
    }
  }, [refreshLists])

  if (!offline) return null

  const open = (entry: RouteEntry) => {
    onOpenRoute({
      from: entry.from,
      to: entry.to,
      people: entry.people ?? 1,
      mode: entry.mode ?? 'tumu',
    })
  }

  return (
    <div
      role="alert"
      className="relative z-20 mx-auto mt-3 w-full max-w-xl px-4 sm:px-6"
    >
      <div className="rounded-2xl border border-amber-500/40 bg-surface-2/95 p-4 shadow-2xl shadow-black/40 backdrop-blur-md">
        <p className="text-sm font-bold text-fg">📡 İnternet Bağlantısı Yok</p>
        <p className="mt-0.5 text-xs text-muted">
          Son rotalarınız cihazda saklı — bağlantı gelince kaldığınız yerden devam edin.
        </p>

        {recent.length > 0 && (
          <>
            <p className="mt-3 text-xs font-bold uppercase tracking-wide text-muted">
              Son Rotalarınız
            </p>
            <div className="mt-1.5 space-y-1.5">
              {recent.map((r, i) => (
                <button
                  key={`${r.from}|${r.to}|${i}`}
                  type="button"
                  onClick={() => open(r)}
                  className="flex w-full items-center gap-2 rounded-xl border border-line/60 bg-bg/40 px-3 py-2 text-left text-xs font-semibold text-fg transition-colors hover:border-accent"
                >
                  <span aria-hidden>🕘</span>
                  <span className="min-w-0 flex-1 truncate">
                    {r.from} → {r.to}
                  </span>
                </button>
              ))}
            </div>
          </>
        )}

        {favorites.length > 0 && (
          <>
            <p className="mt-3 text-xs font-bold uppercase tracking-wide text-muted">
              Favori Duraklar
            </p>
            <div className="mt-1.5 space-y-1.5">
              {favorites.map((r, i) => (
                <button
                  key={`fav|${r.from}|${r.to}|${i}`}
                  type="button"
                  onClick={() => open(r)}
                  className="flex w-full items-center gap-2 rounded-xl border border-line/60 bg-bg/40 px-3 py-2 text-left text-xs font-semibold text-fg transition-colors hover:border-accent"
                >
                  <span aria-hidden>⭐</span>
                  <span className="min-w-0 flex-1 truncate">
                    {r.from} → {r.to}
                  </span>
                </button>
              ))}
            </div>
          </>
        )}

        {recent.length === 0 && favorites.length === 0 && (
          <p className="mt-2 text-xs text-muted">
            Henüz kayıtlı rota yok. Bağlantı gelince aradığınız rotalar burada listelenecek.
          </p>
        )}

        <button
          type="button"
          onClick={() => {
            if (typeof navigator === 'undefined' || navigator.onLine) setOffline(false)
            else refreshLists()
          }}
          className="mt-3 min-h-[40px] w-full rounded-xl bg-accent px-4 text-xs font-bold text-accent-ink"
        >
          Tekrar Dene
        </button>
      </div>
    </div>
  )
}
