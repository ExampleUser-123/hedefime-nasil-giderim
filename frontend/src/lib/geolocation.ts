import { useCallback, useRef, useState } from 'react'
import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'

export type CurrentCoords = { lat: number; lon: number; accuracy?: number }

export type CurrentPositionState = {
  coords: CurrentCoords | null
  error: string | null
  loading: boolean
  refresh: () => void
}

export type GeoErrorType = 'permission' | 'unavailable' | 'timeout' | 'unknown'

export type GeoResult =
  | { ok: true; coords: CurrentCoords }
  | { ok: false; type: GeoErrorType; message: string }

type GeoPosition = {
  coords: { latitude: number; longitude: number; accuracy: number }
}

// GeolocationPositionError kodlarina gore kullanici dostu Turkce mesajlar.
function friendlyGeoMessage(code: number): string {
  switch (code) {
    case 1: // PERMISSION_DENIED
      return 'Konum izni verilmedi. Uygulama ayarlarindan konum iznini acabilirsin.'
    case 2: // POSITION_UNAVAILABLE
      return 'Konum su anda alinamiyor. GPS acik mi kontrol et ve tekrar dene.'
    case 3: // TIMEOUT
      return 'Konum alinirken cok uzun surdu. Lutfen tekrar dene.'
    default:
      return 'Konum alinamadi. Lutfen tekrar dene.'
  }
}

// Native eklenti hatalarini da ayni mesajlara cevirir.
function classifyError(e: unknown): { type: GeoErrorType; message: string } {
  const msg = String((e as { message?: string } | null)?.message ?? e ?? '').toLowerCase()

  if (msg.includes('permission') || msg.includes('denied')) {
    return { type: 'permission', message: friendlyGeoMessage(1) }
  }
  if (msg.includes('unavailable')) {
    return { type: 'unavailable', message: friendlyGeoMessage(2) }
  }
  if (msg.includes('timeout')) {
    return { type: 'timeout', message: friendlyGeoMessage(3) }
  }
  return { type: 'unknown', message: friendlyGeoMessage(0) }
}

/**
 * Android'de konum izni verilmisse true, verilmemisse false dondurur.
 * Web'de her zaman true doner; tarayici kendi dialogunu gosterir.
 */
export async function ensureLocationPermission(): Promise<boolean> {
  if (!Capacitor.isNativePlatform()) return true
  const status = await Geolocation.checkPermissions()
  if (status.location === 'granted' || status.coarseLocation === 'granted') return true
  const req = await Geolocation.requestPermissions()
  return req.location === 'granted' || req.coarseLocation === 'granted'
}

/**
 * Daha dogru konum almak icin kisa bir sure (max 6 sn) boyunca birden fazla
 * GPS ornegi toplar ve accuracy degeri en dusuk (en iyi) olani dondurur.
 * Telefonun GPS'i henuz sabitlenmemisse ilk gelen konum 1-2 km sapabiliyor;
 * bu fonksiyon o sapmayi onemli olcude azaltir.
 */
export async function getAccuratePosition(options?: {
  /** Toplam bekleme suresi (ms). Varsayilan 6000. */
  timeoutMs?: number
  /** Son kabul edilebilir accuracy (metre). Varsayilan 50. */
  desiredAccuracy?: number
  /** Her ornek arasi minimum bekleme (ms). Varsayilan 600. */
  sampleIntervalMs?: number
}): Promise<GeoResult> {
  const timeoutMs = options?.timeoutMs ?? 6000
  const desiredAccuracy = options?.desiredAccuracy ?? 50
  const sampleIntervalMs = options?.sampleIntervalMs ?? 600
  const native = Capacitor.isNativePlatform()

  if (!native && (typeof navigator === 'undefined' || !navigator.geolocation)) {
    return { ok: false, type: 'unavailable', message: friendlyGeoMessage(2) }
  }

  let permissionOk = false
  try {
    permissionOk = await ensureLocationPermission()
  } catch (e) {
    return { ok: false, ...classifyError(e) }
  }

  if (!permissionOk) {
    return { ok: false, type: 'permission', message: friendlyGeoMessage(1) }
  }

  const samples: GeoPosition[] = []
  const startedAt = Date.now()

  const collectOne = (): Promise<GeoPosition | null> =>
    new Promise((resolve) => {
      const onPos = (pos: GeoPosition) => {
        // Android'de zaman zaman 0/0 koordinat gelir; bunlari at
        if (!pos.coords.latitude && !pos.coords.longitude) return resolve(null)
        resolve(pos)
      }
      const onErr = () => resolve(null)
      const opts = {
        enableHighAccuracy: true,
        timeout: Math.max(3000, timeoutMs - (Date.now() - startedAt)),
        maximumAge: 0,
      }
      if (native) {
        Geolocation.getCurrentPosition(opts).then(onPos).catch(onErr)
      } else {
        navigator.geolocation.getCurrentPosition(onPos, onErr, opts)
      }
    })

  // Iki yontemden biriyle toplama yap:
  // A) watchPosition ile surekli ornek al, B) interval ile tek tek al.
  // Native'de watchPosition daha kararli oldugu icin onu tercih edelim.
  if (native) {
    return new Promise((resolve) => {
      let watchId: string | null = null
      const done = (result: GeoResult) => {
        if (watchId) Geolocation.clearWatch({ id: watchId })
        resolve(result)
      }

      const timer = setTimeout(() => {
        if (samples.length) {
          const best = samples.sort((a, b) => a.coords.accuracy - b.coords.accuracy)[0]
          done({ ok: true, coords: { lat: best.coords.latitude, lon: best.coords.longitude, accuracy: best.coords.accuracy } })
        } else {
          done({ ok: false, type: 'timeout', message: friendlyGeoMessage(3) })
        }
      }, timeoutMs)

      Geolocation.watchPosition(
        { enableHighAccuracy: true, timeout: 3000, maximumAge: 0 },
        (pos) => {
          if (!pos) return
          samples.push(pos)
          const best = samples.sort((a, b) => a.coords.accuracy - b.coords.accuracy)[0]
          if (best.coords.accuracy <= desiredAccuracy) {
            clearTimeout(timer)
            done({ ok: true, coords: { lat: best.coords.latitude, lon: best.coords.longitude, accuracy: best.coords.accuracy } })
          }
        },
      ).then((id) => {
        watchId = id
      }).catch((e) => {
        clearTimeout(timer)
        done({ ok: false, ...classifyError(e) })
      })
    })
  }

  // Web tarayici: interval ile ornek topla
  while (Date.now() - startedAt < timeoutMs) {
    const pos = await collectOne()
    if (pos) {
      samples.push(pos)
      if (pos.coords.accuracy <= desiredAccuracy) {
        return { ok: true, coords: { lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy } }
      }
    }
    await new Promise((r) => setTimeout(r, sampleIntervalMs))
  }

  if (samples.length) {
    const best = samples.sort((a, b) => a.coords.accuracy - b.coords.accuracy)[0]
    return { ok: true, coords: { lat: best.coords.latitude, lon: best.coords.longitude, accuracy: best.coords.accuracy } }
  }

  return { ok: false, type: 'timeout', message: friendlyGeoMessage(3) }
}

/**
 * Cihaz konumunu bir kez alir. Android/iOS'ta Capacitor Geolocation eklentisi
 * (izin istemini kendisi yonetir), tarayicida navigator.geolocation kullanir.
 */
export function useCurrentPosition(): CurrentPositionState {
  const [coords, setCoords] = useState<CurrentCoords | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const requestRef = useRef(0)

  const refresh = useCallback(() => {
    const generation = ++requestRef.current
    setLoading(true)
    setError(null)

    getAccuratePosition({ timeoutMs: 7000, desiredAccuracy: 60 })
      .then((res) => {
        if (requestRef.current !== generation) return
        if (res.ok) {
          setCoords(res.coords)
          setError(null)
        } else {
          setCoords(null)
          setError(res.message)
        }
        setLoading(false)
      })
      .catch(() => {
        if (requestRef.current !== generation) return
        setCoords(null)
        setError(friendlyGeoMessage(0))
        setLoading(false)
      })
  }, [])

  return { coords, error, loading, refresh }
}

/**
 * Tek seferlik konum alma helper'i. Bilesen icindeki lokal
 * navigator.geolocation.getCurrentPosition cagrilarinin yerine gecer.
 */
export async function getCurrentLocation(): Promise<GeoResult> {
  return getAccuratePosition({ timeoutMs: 7000, desiredAccuracy: 60 })
}
