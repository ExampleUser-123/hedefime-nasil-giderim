import { Capacitor } from '@capacitor/core'
import { Geolocation } from '@capacitor/geolocation'
import { LocalNotifications } from '@capacitor/local-notifications'

export type GetOffCoords = { lat: number; lon: number }

// Hedef duraga bu mesafeden yakinsiysa (metre) uyar ver.
const ALERT_RADIUS_M = 300
// Izleme sirasinda konum ornekleme araligi (ms).
const WATCH_INTERVAL_MS = 8000

export function distanceMeters(
  a: { lat: number; lon: number },
  b: { lat: number; lon: number },
): number {
  const R = 6371000
  const dLat = ((b.lat - a.lat) * Math.PI) / 180
  const dLon = ((b.lon - a.lon) * Math.PI) / 180
  const lat1 = (a.lat * Math.PI) / 180
  const lat2 = (b.lat * Math.PI) / 180
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

async function ensureNotifyPermission(): Promise<boolean> {
  if (!Capacitor.isNativePlatform()) return true

  const cur = await LocalNotifications.checkPermissions()
  if (cur.display === 'granted') return true

  const req = await LocalNotifications.requestPermissions()
  return req.display === 'granted'
}

async function fireArrivedNotification(label: string): Promise<void> {
  try {
    if (Capacitor.isNativePlatform()) {
      await LocalNotifications.createChannel({
        id: 'inme_uyarisi',
        name: 'İnme uyarısı',
        importance: 5, // HIGH
        visibility: 1, // PUBLIC
        vibration: true,
      }).catch(() => {})
    }

    await LocalNotifications.schedule({
      notifications: [
        {
          id: 990_001, // tek seferlik anlik uyarı; sabit id yeterli
          title: '🚏 İneceğin durak yaklaşıyor!',
          body: `${label} durağına yaklaştın — inmeye hazırlan.`,
          channelId: 'inme_uyarisi',
        },
      ],
    })
  } catch {
    // bildirim gecemedi bile olsa izleme zaten kapanacak
  }
}

export type GetOffWatch = {
  id: string | number
}

export type GetOffEvents = {
  onDistance: (meters: number) => void
  onArrived: () => void
  onError: (message: string) => void
}

/**
 * Kullanicinin KENDI GPS konumunu izler; hedef duraga ALERT_RADIUS_M
 * kadar yaklasinca bildirim atar ve izlemeyi bitirir.
 * Donus degeri: izlemeyi durdurmak icin cagrilan temizleyici.
 */
export async function watchGetOff(
  destination: GetOffCoords,
  label: string,
  events: GetOffEvents,
): Promise<() => void> {
  const notifyOk = await ensureNotifyPermission()

  // Hem Capacitor hem DOM geolocation tipleriyle uyumlu notr konum tipi
  type PosLike = { coords: { latitude: number; longitude: number } }

  const handle = (position: PosLike | null) => {
    if (!position) return
    const meters = distanceMeters(
      { lat: position.coords.latitude, lon: position.coords.longitude },
      destination,
    )
    events.onDistance(meters)

    if (meters <= ALERT_RADIUS_M) {
      if (notifyOk) void fireArrivedNotification(label)
      events.onArrived()
    }
  }

  const handleError = (e: GeolocationPositionError) => {
    events.onError(
      e.code === 1
        ? 'Konum izni verilmedi; inme uyarısı için izin gerekli.'
        : 'Konum şu anda alınamıyor. GPS açık mı kontrol et.',
    )
  }

  if (Capacitor.isNativePlatform()) {
    const status = await Geolocation.checkPermissions()
    if (status.location !== 'granted' && status.coarseLocation !== 'granted') {
      await Geolocation.requestPermissions()
    }

    const watchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true, interval: WATCH_INTERVAL_MS, maximumAge: 5000 },
      handle,
    )

    // Eklenti hatalarini yakalamanin dogrudan yolu yok; ilk konum gelmezse
    // 60 sn sonra tek seferlik kontrol denemesi yap.
    const fallback = setTimeout(async () => {
      try {
        const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true, timeout: 10000 })
        handle(pos)
      } catch {
        events.onError('Konum alınamadı. Açık alanda tekrar dene.')
      }
    }, 60000)

    return () => {
      clearTimeout(fallback)
      void Geolocation.clearWatch({ id: watchId }).catch(() => {})
    }
  }

  if (typeof navigator === 'undefined' || !navigator.geolocation) {
    events.onError('Cihazın konum desteği yok.')
    return () => {}
  }

  const watchId = navigator.geolocation.watchPosition(handle, handleError, {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 5000,
  })

  return () => navigator.geolocation.watchPosition != null && navigator.geolocation.clearWatch(watchId)
}
