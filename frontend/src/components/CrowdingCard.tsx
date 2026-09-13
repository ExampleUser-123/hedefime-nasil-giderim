import { useEffect, useState, type ReactElement } from 'react'
import {
  fetchCrowdingSummary,
  postCrowding,
  type CrowdingLevel,
} from '@/lib/api'

const LEVELS: { id: CrowdingLevel; label: string; emoji: string }[] = [
  { id: 'empty', label: 'Boş', emoji: '🟢' },
  { id: 'normal', label: 'Normal', emoji: '🟡' },
  { id: 'crowded', label: 'Kalabalık', emoji: '🟠' },
  { id: 'packed', label: 'Tıklım tıklım', emoji: '🔴' },
]

function todayKey(): string {
  return new Date().toISOString().slice(0, 10)
}

export default function CrowdingCard({
  city,
  lines,
}: {
  city: string
  lines: string[]
}): ReactElement | null {
  const [rated, setRated] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [summary, setSummary] = useState<Record<string, { total: number; counts: Record<string, number>; crowded_share: number }>>({})

  const key = lines[0] ?? ''
  const throttled = (() => {
    try {
      return localStorage.getItem(`hng-crowd-${city}|${key}`) === todayKey()
    } catch {
      return false
    }
  })()

  useEffect(() => {
    let cancelled = false
    fetchCrowdingSummary(city, lines)
      .then((s) => {
        if (!cancelled) setSummary(s)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city, lines.join('|')])

  async function rate(level: CrowdingLevel) {
    if (sending || rated) return
    setSending(true)
    try {
      await postCrowding(city, key, level)
      setRated(level)
      try {
        localStorage.setItem(`hng-crowd-${city}|${key}`, todayKey())
      } catch {
        // localStorage kapaliysa sessiz gec
      }
    } catch {
      // hata durumunda sessiz gec
    } finally {
      setSending(false)
    }
  }

  if (!key) return null

  const stat = summary[key]
  const busyLabel =
    stat == null
      ? null
      : stat.crowded_share >= 0.6
        ? 'Genelde kalabalık'
        : stat.crowded_share >= 0.3
          ? 'Değişken'
          : 'Genelde rahat'

  return (
    <div className="mt-4 rounded-2xl border border-line bg-surface-2/90 px-4 py-3">
      <p className="text-xs font-bold text-accent">👥 Topluluk doluluk bilgisi</p>

      {stat && (
        <p className="mt-1 text-xs text-muted">
          Son 7 günde {stat.total} kişi oy verdi — <b className="text-text">{busyLabel}</b>
          {stat.counts.crowded + stat.counts.packed > 0 && (
            <> · %{Math.round(stat.crowded_share * 100)} kalabalık dedi</>
          )}
        </p>
      )}

      {throttled && !rated ? (
        <p className="mt-1.5 text-xs text-muted">Bugün bu hat için bildirim yaptın — teşekkürler!</p>
      ) : rated ? (
        <p className="mt-1.5 text-xs text-accent">Teşekkürler! Bildirğin topluluğa kaydedildi ✓</p>
      ) : (
        <>
          <p className="mt-1.5 text-xs text-muted">
            Bu hattı bugün kullandıysan: araç nasıldı?
          </p>
          <div className="mt-2 grid grid-cols-4 gap-1.5">
            {LEVELS.map((lvl) => (
              <button
                key={lvl.id}
                type="button"
                disabled={sending}
                onClick={() => void rate(lvl.id)}
                className="rounded-xl border border-line py-2 text-center text-[11px] font-bold text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-40"
              >
                <span className="block text-base">{lvl.emoji}</span>
                {lvl.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
