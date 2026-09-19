import { createContext, useContext, useEffect, useRef, useState, type ReactElement } from 'react'
import { fetchNextDepartures, type NextDeparture } from '@/lib/api'
import { liveMinutesAhead } from '@/lib/departureTime'

// Rotanin bulundugu sehri ust bileşenden almak icin baglam.
export const DepartureCityContext = createContext<string>('')

// Promise cache (90 sn TTL): ayni sehir/hat/durak icin tekrar istek atilmaz,
// ancak veri bayatlayinca tazelenir.
const CACHE_TTL_MS = 90000
const departureCache = new Map<string, { at: number; promise: Promise<NextDeparture[] | null> }>()

function getDepartures(
  city: string,
  line: string,
  stop: string,
  lat?: number,
  lon?: number,
): Promise<NextDeparture[] | null> {
  const key = `${city}|${line}|${stop}`

  const now = Date.now()
  let cached = departureCache.get(key)

  if (!cached || now - cached.at > CACHE_TTL_MS) {
    cached = {
      at: now,
      promise: fetchNextDepartures(city, line, stop, lat, lon)
        .then((data) => (data?.departures?.length ? data.departures : null))
        .catch(() => null),
    }
    departureCache.set(key, cached)
  }

  return cached.promise
}

// Bus leg kartina eklenen kompakt "yaklaşan sefer" rozeti.
// Veri yoksa (istek null donerse) hic render etmez.
export function DepartureBadge({
  line,
  stop,
  lat,
  lon,
}: {
  line: string | null
  stop: string | null
  lat?: number
  lon?: number
}): ReactElement | null {
  const city = useContext(DepartureCityContext)
  const [departure, setDeparture] = useState<NextDeparture | null>(null)
  const aliveRef = useRef(true)

  useEffect(() => {
    aliveRef.current = true

    if (!city || !line || !stop) return undefined

    getDepartures(city, line, stop, lat, lon).then((departures) => {
      if (aliveRef.current && departures && departures.length > 0) {
        setDeparture(departures[0])
      }
    })

    return () => {
      aliveRef.current = false
    }
  }, [city, line, stop, lat, lon])

  if (!departure) return null

  // Cihaz saatine gore guncel kalan sure; gecmise dusmusse rozeti gizle.
  const liveAhead = liveMinutesAhead(departure, Date.now())
  if (liveAhead < 0) return null

  if (departure.source === 'tahmini') {
    return (
      <span
        className="rounded-full bg-bg/60 px-2 py-0.5 text-xs italic text-muted tabular-nums"
        title={`Tahmini kalkış: ${departure.time}`}
      >
        ~{liveAhead} dk (tahmini)
      </span>
    )
  }

  return (
    <span
      className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums"
      title={`Kalkış saati: ${departure.time}`}
    >
      ⏱ {liveAhead} dk
    </span>
  )
}
