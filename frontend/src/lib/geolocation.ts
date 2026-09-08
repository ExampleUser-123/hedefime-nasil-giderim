import { useCallback, useEffect, useRef, useState } from 'react'
import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'

export type CurrentCoords = { lat: number; lon: number }

export type CurrentPositionState = {
  coords: CurrentCoords | null
  error: string | null
  loading: boolean
  refresh: () => void
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
function friendlyErrorFromException(e: unknown): string {
  const msg = String((e as { message?: string } | null)?.message ?? e ?? '').toLowerCase()

  if (msg.includes('permission') || msg.includes('denied')) {
    return friendlyGeoMessage(1)
  }
  if (msg.includes('unavailable')) {
    return friendlyGeoMessage(2)
  }
  if (msg.includes('timeout')) {
    return friendlyGeoMessage(3)
  }
  return friendlyGeoMessage(0)
}

/**
 * Cihaz konumunu bir kez alir. Android/iOS'ta Capacitor Geolocation eklentisi
 * (izin istemini kendisi yonetir), tarayicida navigator.geolocation kullanir.
 */
export function useCurrentPosition(): CurrentPositionState {
  const [coords, setCoords] = useState<CurrentCoords | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const native = Capacitor.isNativePlatform()
  // istek nesli sayaci: refresh() yeni cagrildiginda eski cevaplari yok sayar
  const requestRef = useRef(0)

  useEffect(() => {
    return () => {
      requestRef.current++
    }
  }, [])

  const refresh = useCallback(() => {
    if (!native && (typeof navigator === 'undefined' || !navigator.geolocation)) {
      setError('Cihazin konum destegi yok.')
      setCoords(null)
      setLoading(false)
      return
    }

    const generation = ++requestRef.current

    setLoading(true)
    setError(null)

    // Native eklenti timeout'u + pay; cozulmezse mesaj gösterilir.
    const guard = setTimeout(() => {
      if (requestRef.current !== generation) return
      setCoords(null)
      setError("Konum şu anda alınamadı. Açık alanda birkaç saniye bekleyip Yenile'ye bas.")
      setLoading(false)
    }, 16000)

    ;(async () => {
      try {
        // Android'de eklenti izni kendiliginden sormaz; once acikca iste.
        if (native) {
          const status = await Geolocation.checkPermissions()
          if (status.location !== 'granted' && status.coarseLocation !== 'granted') {
            await Geolocation.requestPermissions()
          }
        }

        const position = native
          ? await Geolocation.getCurrentPosition({
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 30000,
            })
          : await new Promise<GeolocationPosition>((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 30000,
              })
            })

        clearTimeout(guard)
        if (requestRef.current !== generation) return

        setCoords({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        })
        setError(null)
        setLoading(false)
      } catch (e) {
        clearTimeout(guard)
        if (requestRef.current !== generation) return

        setCoords(null)
        setError(friendlyErrorFromException(e))
        setLoading(false)
      }
    })()
  }, [native])

  return { coords, error, loading, refresh }
}
