import { useState, type ReactElement } from 'react'

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)

  if (hours === 0) return `${mins} dk`

  return `${hours} sa ${String(mins).padStart(2, '0')} dk`
}

function formatMeters(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`

  return `${(meters / 1000).toFixed(1).replace('.', ',')} km`
}

function formatTL(value: number): string {
  return `${Math.round(value).toLocaleString('tr-TR')} TL`
}

export default function TripReport({
  from,
  to,
  people,
  totalMinutes,
  walkingDistanceM,
  costPerPerson,
  totalCost,
  legsCount,
}: {
  from: string
  to: string
  people: number
  totalMinutes: number | null
  walkingDistanceM: number | null
  costPerPerson: number | null
  totalCost: number | null
  legsCount: number
}): ReactElement {
  const [copied, setCopied] = useState(false)

  function buildReportText(): string {
    const lines: string[] = []

    lines.push(`📍 ${from} → ${to} (${people} kişi)`)

    if (totalMinutes != null) lines.push(`⏱ Süre: ${formatDuration(totalMinutes)}`)

    if (walkingDistanceM != null)
      lines.push(`🚶 Yürüyüş: ${formatMeters(walkingDistanceM)}`)

    lines.push(`🚌 ${legsCount} adım`)

    if (costPerPerson != null)
      lines.push(`💰 Kişi başı: ~${formatTL(costPerPerson)}`)

    if (totalCost != null) lines.push(`💰 Toplam: ~${formatTL(totalCost)}`)

    lines.push('')
    lines.push('Hedefime Nasıl Giderim ile hesaplandı')

    return lines.join('\n')
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(buildReportText())
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // panoya erisilemezse sessiz gec
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-xs font-bold uppercase tracking-wide text-accent">
        📋 Yolculuk raporu
      </p>

      <p className="mt-2 break-words text-sm font-bold">
        {from}
        <span className="mx-1.5 text-accent">→</span>
        {to}
        <span className="ml-2 text-xs font-normal text-muted">
          ({people} kişi)
        </span>
      </p>

      <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
        {totalMinutes != null && (
          <div className="rounded-xl border border-line px-3 py-2">
            <p className="text-xs text-muted">Süre</p>
            <p className="font-bold tabular-nums">
              {formatDuration(totalMinutes)}
            </p>
          </div>
        )}
        {walkingDistanceM != null && (
          <div className="rounded-xl border border-line px-3 py-2">
            <p className="text-xs text-muted">Yürüyüş</p>
            <p className="font-bold tabular-nums">
              {formatMeters(walkingDistanceM)}
            </p>
          </div>
        )}
        {costPerPerson != null && (
          <div className="rounded-xl border border-line px-3 py-2">
            <p className="text-xs text-muted">Kişi başı</p>
            <p className="font-bold tabular-nums">~{formatTL(costPerPerson)}</p>
          </div>
        )}
        {totalCost != null && (
          <div className="rounded-xl border border-line px-3 py-2">
            <p className="text-xs text-muted">Toplam ({people} kişi)</p>
            <p className="font-bold text-accent tabular-nums">
              ~{formatTL(totalCost)}
            </p>
          </div>
        )}
      </div>

      <p className="mt-3 text-xs text-muted">{legsCount} adım</p>

      <button
        type="button"
        onClick={handleCopy}
        className="mt-3 flex min-h-[44px] w-full items-center justify-center gap-1.5 rounded-xl border border-line bg-bg text-sm font-bold text-accent transition-colors hover:bg-accent/10"
      >
        {copied ? 'Kopyalandı ✓' : 'Raporu kopyala'}
      </button>
    </div>
  )
}
