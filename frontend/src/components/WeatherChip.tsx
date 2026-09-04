import { useEffect, useState } from 'react'
import { fetchWeather, type Weather } from '@/lib/api'
import { IconCloud, IconRain, IconSun } from '@/icons'

function WeatherIcon({ condition, className }: { condition: string | null; className?: string }) {
  if (!condition) return <IconCloud className={className} />

  const text = condition.toLowerCase()

  if (text.includes('yağmur') || text.includes('sağanak') || text.includes('çiseleme') || text.includes('kar')) {
    return <IconRain className={className} />
  }

  if (text.includes('açık') || text.includes('güneşli')) {
    return <IconSun className={className} />
  }

  return <IconCloud className={className} />
}

export default function WeatherChip() {
  const [weather, setWeather] = useState<Weather | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false

    fetchWeather('İstanbul')
      .then((data) => {
        if (!cancelled) setWeather(data)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (failed || !weather) {
    return null
  }

  return (
    <div className="flex items-center gap-2 rounded-full border border-line bg-surface/80 px-3.5 py-2 backdrop-blur-sm">
      <WeatherIcon condition={weather.current.condition} className="h-4 w-4 text-accent" />
      <span className="text-sm font-semibold tabular-nums">
        {Math.round(weather.current.temperature)}°
      </span>
      <span className="hidden text-xs text-muted sm:inline">İstanbul</span>
    </div>
  )
}
