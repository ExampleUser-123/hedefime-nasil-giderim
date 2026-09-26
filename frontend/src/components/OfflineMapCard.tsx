import { useEffect, useState, type ReactElement } from 'react'
import { fetchXpStore } from '@/lib/api'
import { getStoredUser } from '@/lib/auth'
import { getCurrentLocation } from '@/lib/geolocation'
import {
  clearPack,
  downloadPack,
  getPackMeta,
  type TilePackMeta,
} from '@/lib/offlineTiles'

/**
 * Cevrimdisi harita paketi (XP Magazasi offline_map urunu).
 * Giris yapmis ama paketi olmayan kullaniciya kilit gosterir.
 */
export default function OfflineMapCard(): ReactElement {
  const [locked, setLocked] = useState(false)
  const [meta, setMeta] = useState<TilePackMeta | null>(() => getPackMeta())
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!getStoredUser()) return
    fetchXpStore()
      .then((data) => {
        if (!data.items.some((i) => i.id === 'offline_map' && i.owned)) {
          setLocked(true)
        }
      })
      .catch(() => {})
  }, [])

  async function download() {
    setBusy(true)
    setError(null)
    setProgress('Konum alınıyor…')
    try {
      const loc = await getCurrentLocation()
      if (!loc.ok) {
        setError('Konum alınamadı. GPS izni verip tekrar dene.')
        return
      }
      const res = await downloadPack(loc.coords.lat, loc.coords.lon, (done, total) => {
        setProgress(`Karolar indiriliyor… ${done}/${total}`)
      })
      setMeta(getPackMeta())
      setProgress(res.count > 0 ? null : 'Hiç karo indirilemedi.')
      if (res.count === 0) setError('İndirme başarısız. İnterneti kontrol edip tekrar dene.')
    } catch {
      setError('İndirme başarısız. İnterneti kontrol edip tekrar dene.')
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    try {
      await clearPack()
      setMeta(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">🗺 Çevrimdışı harita</p>
      <p className="mt-1 text-xs text-muted">
        Bulunduğun çevrenin harita karolarını telefona indir; internetsiz
        kaldığında harita bu bölgede çalışmaya devam eder.
      </p>

      {locked ? (
        <p className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2.5 text-xs text-amber-200">
          🔒 Çevrimdışı harita indirmek için XP Mağazasından paketi aç (600 XP).
        </p>
      ) : meta ? (
        <div className="mt-3 flex items-center justify-between gap-2 rounded-xl border border-line/60 bg-bg/40 px-3 py-2">
          <p className="text-xs font-bold">
            {meta.count} karo indirildi
            <span className="block text-[11px] font-normal text-muted">
              {new Date(meta.at).toLocaleDateString('tr-TR')} · çevren
            </span>
          </p>
          <button
            type="button"
            onClick={() => void remove()}
            disabled={busy}
            className="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-[11px] font-bold text-muted transition-colors hover:border-red-400/50 hover:text-red-300 disabled:opacity-40"
          >
            Sil
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => void download()}
          disabled={busy}
          className="mt-3 flex min-h-[44px] w-full items-center justify-center rounded-xl bg-accent text-sm font-bold text-accent-ink disabled:opacity-50"
        >
          {busy ? (progress ?? 'İndiriliyor…') : '⬇ Çevremi indir'}
        </button>
      )}
      {busy && progress && meta === null && (
        <p className="mt-2 text-xs text-muted">{progress}</p>
      )}
      {error && <p role="alert" className="mt-2 text-xs text-red-300">{error}</p>}
    </div>
  )
}
