import { useCallback, useEffect, useRef, useState } from 'react'

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
      return 'Konum izni verilmedi. Tarayici/uygulama ayarlarindan konum iznini acabilirsin.'
    case 2: // POSITION_UNAVAILABLE
      return 'Konum su anda alinamiyor. GPS acik mi kontrol et ve tekrar dene.'
    case 3: // TIMEOUT
      return 'Konum alinirken cok uzun surdu. Lutfen tekrar dene.'
    default:
      return 'Konum alinamadi. Lutfen tekrar dene.'
  }
}

/**
 * Cihaz konumunu bir kez alir (getCurrentPosition; Capacitor WebView destekler,
 * watchPosition kullanilmaz). Hata durumunda null coords + Turkce hata mesaji doner.
 */
export function useCurrentPosition(): CurrentPositionState {
  const [coords, setCoords] = useState<CurrentCoords | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  // getCurrentPosition'in dogrudan iptal API'si yok; timeout'tan sonra gelen
  // gec cevaplari yoksaymak icin kullanilir.
  const inFlightRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearInFlight = useCallback(() => {
    if (inFlightRef.current !== null) {
      clearTimeout(inFlightRef.current)
      inFlightRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      // Cleanup: bekleyen istekler iptal edilir.
      clearInFlight()
    }
  }, [clearInFlight])

  const refresh = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setError('Cihazin konum destegi yok.')
      setCoords(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    clearInFlight()

    const timerId = setTimeout(() => {
      inFlightRef.current = null
      setLoading(false)
    }, 16000) // options.timeout (15s) + pay
    inFlightRef.current = timerId

    navigator.geolocation.getCurrentPosition(
      (position) => {
        // Istek zaman asimiyla iptal edildiyse gec cevabi yoksay.
        if (inFlightRef.current === null) return
        clearInFlight()
        setCoords({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        })
        setError(null)
        setLoading(false)
      },
      (err) => {
        if (inFlightRef.current === null) return
        clearInFlight()
        setCoords(null)
        setError(friendlyGeoMessage(err.code))
        setLoading(false)
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 },
    )
  }, [clearInFlight])

  return { coords, error, loading, refresh }
}
