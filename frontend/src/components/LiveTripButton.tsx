import { useEffect, useRef, useState, type ReactElement } from 'react'
import { API_BASE, createLiveTrip, pingLiveTrip, type PlanResult } from '@/lib/api'
import { getCurrentLocation } from '@/lib/geolocation'

/** Haversine (m) — ETA tahmini icin. */
function distanceM(aLat: number, aLon: number, bLat: number, bLon: number): number {
  const r = 6371000
  const p1 = (aLat * Math.PI) / 180
  const p2 = (bLat * Math.PI) / 180
  const dphi = ((bLat - aLat) * Math.PI) / 180
  const dl = ((bLon - aLon) * Math.PI) / 180
  const h =
    Math.sin(dphi / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2
  return 2 * r * Math.asin(Math.sqrt(h))
}

/**
 * Aktif rotada "Yolculuğumu Paylaş": takip linki uretir, konum + tahmini
 * varis suresini periyodik gonderir. Kapatilinca gonderim durur.
 */
export default function LiveTripButton({
  plan,
  onRequireLogin,
}: {
  plan: PlanResult
  onRequireLogin: () => void
}): ReactElement {
  const [tripId, setTripId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [shared, setShared] = useState(false)
  const keyRef = useRef<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  function stopPing() {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  useEffect(() => stopPing, [])

  async function pingOnce() {
    if (!keyRef.current || !tripId) return
    const loc = await getCurrentLocation()
    if (!loc.ok) return
    const { lat, lon } = loc.coords
    const dest = plan.end_coord
    const eta =
      dest && typeof dest.lat === 'number'
        ? Math.max(1, Math.round(distanceM(lat, lon, dest.lat, dest.lon) / 25000 * 60))
        : null
    await pingLiveTrip(tripId as string, {
      update_key: keyRef.current as string,
      lat,
      lon,
      eta_min: eta,
    })
  }

  async function start() {
    if (busy || tripId) return
    setBusy(true)
    setError(null)
    try {
      const loc = await getCurrentLocation()
      if (!loc.ok) {
        setError(loc.message)
        return
      }
      const dest = plan.end_coord
      const trip = await createLiveTrip({
        from: plan.start,
        destination: plan.destination,
        dest_lat: dest?.lat ?? null,
        dest_lon: dest?.lon ?? null,
        lat: loc.coords.lat,
        lon: loc.coords.lon,
        eta_min: null,
      })
      if (!trip) throw new Error('Takip başlatılamadı. Lütfen tekrar deneyin.')
      keyRef.current = trip.update_key
      setTripId(trip.id)
      const url = `${API_BASE}/live-trips/${trip.id}/view`
      const text = `Canlı konumumu takip et: ${plan.start} → ${plan.destination}\n${url}`
      try {
        if (typeof navigator !== 'undefined' && navigator.share) {
          await navigator.share({ title: 'Canlı Yolculuk', text })
        } else {
          await navigator.clipboard.writeText(text)
          setShared(true)
          setTimeout(() => setShared(false), 2500)
        }
      } catch {
        // paylasim iptal edildiyse sessiz gec (takip yine de acik)
      }
      await pingOnce()
      timerRef.current = setInterval(() => {
        void pingOnce()
      }, 60000)
    } catch (e) {
      const err = e as Error & { status?: number }
      if (err.status === 401) {
        onRequireLogin()
        return
      }
      setError(err.message || 'Takip başlatılamadı.')
    } finally {
      setBusy(false)
    }
  }

  function stop() {
    stopPing()
    keyRef.current = null
    setTripId(null)
  }

  if (tripId) {
    return (
      <div className="flex items-center gap-2">
        <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
        </span>
        <span className="text-xs font-bold text-emerald-300">Canlı paylaşımda</span>
        <button
          type="button"
          onClick={stop}
          className="rounded-lg border border-line px-2 py-1 text-[11px] text-muted"
        >
          Durdur
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => void start()}
        disabled={busy}
        className="rounded-xl border border-accent/40 px-3 py-2 text-xs font-bold text-accent disabled:opacity-50"
      >
        {busy ? 'Açılıyor…' : '📡 Yolculuğumu Paylaş'}
      </button>
      {(error || shared) && (
        <p className={`mt-1 text-[11px] ${error ? 'text-red-300' : 'text-emerald-300'}`}>
          {error ?? 'Link panoya kopyalandı.'}
        </p>
      )}
    </div>
  )
}
