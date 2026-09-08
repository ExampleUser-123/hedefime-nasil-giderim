import { createContext, useContext, useEffect, useRef, useState, type ReactElement } from 'react'
import { fetchNextDepartures, type NextDeparture } from '@/lib/api'

// Rotanin bulundugu sehri ust bileşenden almak icin baglam.
export const DepartureCityContext = createContext<string>('')

// Promise cache: ayni sehir/hat/durak icin tekrar istek atilmaz.
const departureCache = new Map<string, Promise<NextDeparture[] | null>>()

function getDepartures(
  city: string,
  line: string,
  stop: string,
  lat?: number,
  lon?: number,
): Promise<NextDeparture[] | null> {
  const key = `${city}|${line}|${stop}`

  let cached = departureCache.get(key)

  if (!cached) {
    cached = fetchNextDepartures(city, line, stop, lat, lon)
      .then((data) => (data?.departures?.length ? data.departures : null))
      .catch(() => null)
    departureCache.set(key, cached)
  }

  return cached
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

  if (departure.source === 'tahmini') {
    return (
      <span
        className="rounded-full bg-bg/60 px-2 py-0.5 text-xs italic text-muted tabular-nums"
        title={`Tahmini kalkış: ${departure.time}`}
      >
        ~{departure.minutes_ahead} dk (tahmini)
      </span>
    )
  }

  return (
    <span
      className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums"
      title={`Kalkış saati: ${departure.time}`}
    >
      ⏱ {departure.minutes_ahead} dk
    </span>
  )
}
