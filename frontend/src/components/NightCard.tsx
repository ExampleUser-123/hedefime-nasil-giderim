import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchNearbyStops,
  fetchStopDepartures,
  fetchXpStore,
  type StopDeparture,
} from '@/lib/api'
import { getStoredUser } from '@/lib/auth'
import { getCurrentLocation } from '@/lib/geolocation'
import { getPinnedPlace } from '@/lib/storage'
import { clockAfter, ISTANBUL_TZ, liveMinutesAhead } from '@/lib/departureTime'
import { goToPlace } from '@/lib/navigate'

function istanbulHour(nowMs: number): number {
  const parts = new Intl.DateTimeFormat('tr-TR', {
    timeZone: ISTANBUL_TZ,
    hour: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(new Date(nowMs))
  return Number(parts.find((p) => p.type === 'hour')?.value ?? '0')
}

type LateItem = StopDeparture & { stopName: string }

/**
 * Gece Modu: Istanbul saatiyle 22:00'den sonra ana sayfada belirir.
 * Yakin duraklarin gec seferlerini geri sayimla gosterir + Eve Git kisayolu.
 * Kota yemeyen uclari kullanir (nearby-stops, stop-departures).
 */
export default function NightCard({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}): ReactElement | null {
  const [nowMs, setNowMs] = useState(() => Date.now())
  const [items, setItems] = useState<LateItem[] | null>(null)
  const [going, setGoing] = useState(false)
  const [goError, setGoError] = useState<string | null>(null)
  // XP Mağazası "Son Sefer Erken Uyarısı": kart 22:00 yerine 20:00'de açılır
  const [earlyAlert, setEarlyAlert] = useState(false)
  // "Aptal Hata" Koruma Paketi: en yakın kalkışa 10 dk kala bildirim
  const [guardOwned, setGuardOwned] = useState(false)
  const [alarmSet, setAlarmSet] = useState(false)

  useEffect(() => {
    if (!getStoredUser()) return
    fetchXpStore()
      .then((data) => {
        if (data.items.some((i) => i.id === 'night_alert' && i.owned)) setEarlyAlert(true)
        if (data.items.some((i) => i.id === 'silly_guard' && i.owned)) setGuardOwned(true)
      })
      .catch(() => {})
  }, [])

  // Koruma paketi varsa: en yakın kalkıştan 10 dk önceye bildirim kur
  useEffect(() => {
    if (!guardOwned || !items || items.length === 0 || alarmSet) return
    let cancelled = false
    ;(async () => {
      try {
        const { Capacitor } = await import('@capacitor/core')
        if (!Capacitor.isNativePlatform()) return
        const { LocalNotifications } = await import('@capacitor/local-notifications')
        const perm = await LocalNotifications.checkPermissions()
        if (perm.display !== 'granted') {
          const req = await LocalNotifications.requestPermissions()
          if (req.display !== 'granted') return
        }
        const soonest = [...items].sort(
          (a, b) => liveMinutesAhead(a, Date.now()) - liveMinutesAhead(b, Date.now()),
        )[0]
        const leftMin = liveMinutesAhead(soonest, Date.now())
        if (leftMin <= 0 || leftMin > 120) return
        const at = new Date(Date.now() + Math.max(0, leftMin - 10) * 60_000)
        await LocalNotifications.schedule({
          notifications: [{
            id: 9001,
            title: '🚌 Son sefer alarmı',
            body: `${soonest.line} (${soonest.stopName}) ~10 dk içinde kalkıyor: ${soonest.time}`,
            schedule: { at },
          }],
        })
        if (!cancelled) setAlarmSet(true)
      } catch {
        // bildirim kurulamazsa kart ici geri sayim yine calisir
      }
    })()
    return () => {
      cancelled = true
    }
  }, [guardOwned, items, alarmSet])

  const night = istanbulHour(nowMs) >= (earlyAlert ? 20 : 22)
  const home = getPinnedPlace('home')

  useEffect(() => {
    if (!night) return
    let alive = true
    const timer = setInterval(() => setNowMs(Date.now()), 30000)
    ;(async () => {
      try {
        const loc = await getCurrentLocation()
        if (!alive || !loc.ok) {
          if (alive) setItems([])
          return
        }
        const stops = (await fetchNearbyStops(loc.coords.lat, loc.coords.lon, 3)) ?? []
        const merged: LateItem[] = []
        for (const s of stops) {
          try {
            const deps = (await fetchStopDepartures(s.city, s.name, s.lat, s.lon, s.lines)) ?? []
            for (const d of deps.slice(0, 2)) merged.push({ ...d, stopName: s.name })
          } catch {
            // tek durak patlarsa digerleri devam
          }
          if (!alive) return
        }
        if (alive) {
          merged.sort(
            (a, b) => liveMinutesAhead(a, Date.now()) - liveMinutesAhead(b, Date.now()),
          )
          setItems(merged.slice(0, 4))
        }
      } catch {
        if (alive) setItems([])
      }
    })()
    return () => {
      alive = false
      clearInterval(timer)
    }
  }, [night])

  if (!night) return null

  async function goHome() {
    if (!home || going) return
    setGoing(true)
    setGoError(null)
    try {
      const res = await goToPlace(home.address, onOpenRoute)
      if (!res.ok) setGoError(res.message)
    } finally {
      setGoing(false)
    }
  }

  return (
    <div className="mt-4 rounded-2xl border border-indigo-400/30 bg-indigo-950/40 p-4">
      <p className="text-sm font-bold">
        🌙 Gece Modu — Son Sefer Uyarısı
        {earlyAlert && (
          <span className="ml-2 rounded-full bg-accent/15 px-2 py-0.5 text-[10px] font-bold text-accent">
            Erken uyarı aktif ✓
          </span>
        )}
        {alarmSet && (
          <span className="ml-2 rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] font-bold text-amber-300">
            🔔 Son sefer alarmı kurulu
          </span>
        )}
      </p>
      <p className="mt-0.5 text-xs text-muted">
        Gece seferleri seyrekleşir. Aşağıdaki kalkışlara dikkat edin.
      </p>

      {items === null ? (
        <p className="mt-2 text-xs text-muted">Yakın duraklar kontrol ediliyor…</p>
      ) : items.length === 0 ? (
        <p className="mt-2 text-xs text-muted">
          Yakında gece seferi bilgisi yok — saat bilgisi güncel olmayabilir.
        </p>
      ) : (
        <div className="mt-2 space-y-1.5">
          {items.map((d, i) => {
            const left = liveMinutesAhead(d, nowMs)
            return (
              <div key={`${d.line}-${d.time}-${i}`} className="flex items-center justify-between gap-2 rounded-xl bg-bg/40 px-3 py-2">
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold">
                    {d.line} <span className="font-normal text-muted">· {d.stopName}</span>
                  </p>
                  <p className="text-[11px] text-muted tabular-nums">
                    Kalkış: {d.time}{d.source === 'tahmini' ? ' (tahmini)' : ''}
                  </p>
                </div>
                <span className="shrink-0 rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent tabular-nums">
                  {left <= 0 ? 'şimdi' : `${left} dk`}
                </span>
              </div>
            )
          })}
        </div>
      )}

      {home ? (
        <button
          type="button"
          onClick={() => void goHome()}
          disabled={going}
          className="mt-3 w-full rounded-xl bg-accent py-2.5 text-sm font-bold text-accent-ink disabled:opacity-50"
        >
          {going ? 'Konum alınıyor…' : `🏠 Eve Git (${home.label})`}
        </button>
      ) : (
        <p className="mt-2 text-[11px] text-muted">
          Ev konumu sabitlenirse tek tıkla eve rota kurulur (Profil → Sabit konumlar).
        </p>
      )}
      {goError && (
        <p role="alert" className="mt-2 text-[11px] text-red-300">{goError}</p>
      )}
      <p className="mt-2 text-[11px] text-muted">
        Saat {clockAfter(nowMs, 0)} (İstanbul) itibarıyla gösterilir.
      </p>
    </div>
  )
}
