import { useEffect, useMemo, useRef, useState, type ReactElement } from 'react'

export type VoiceGuidanceLeg = {
  type: string
  name: string | null
  line: string | null
  from_stop?: string | null
  to_stop?: string | null
  distance_m?: number
}

// Tip bazli tasit adlari
function vehicleLabel(type: string, line: string | null): string {
  const t = type.toLowerCase()

  if (t.includes('walk')) return ''
  if (t.includes('metro')) return line ? `${line} metro` : 'metro'
  if (t.includes('tram')) return line ? `${line} tramvayı` : 'tramvay'
  if (t.includes('ferry') || t.includes('vapur') || t.includes('deniz'))
    return line ? `${line} vapuru` : 'vapur'
  if (t.includes('dolmus') || t.includes('dolmuş')) return line ? `${line} dolmuşu` : 'dolmuş'
  if (t.includes('minibus')) return line ? `${line} minibüsü` : 'minibüs'
  if (t.includes('tren') || t.includes('marmaray')) return line ? `${line} treni` : 'tren'
  if (t.includes('teleferik') || t.includes('funic')) return line ? `${line} hattı` : 'teleferik'
  if (t.includes('bus') || t.includes('otobus') || t.includes('otobüs'))
    return line ? `${line} numaralı otobüs` : 'otobüs'

  return line ? `${line} hattı` : 'araca'
}

// Her leg icin Turkce cumle
function legSentence(leg: VoiceGuidanceLeg, index: number, total: number): string {
  const step = `${index + 1}. adım: `

  if (leg.type.toLowerCase().includes('walk')) {
    const meters = leg.distance_m
    const target = leg.to_stop ? `, ${leg.to_stop} durağına varın` : ''

    return `${step}${meters != null ? `${Math.round(meters)} metre yürüyün` : 'yürüyün'}${target}.`
  }

  const vehicle = vehicleLabel(leg.type, leg.line)
  const board = leg.from_stop ? `${vehicle}na ${leg.from_stop} durağında binin` : `${vehicle}na binin`
  const alight = leg.to_stop ? `${leg.to_stop} durağında inin` : ''
  const duration = leg.distance_m != null ? `, yaklaşık ${Math.max(1, Math.round(leg.distance_m / 400))} dakika` : ''
  const more = index < total - 1 ? ' Ardından devam edin.' : ' Yolculuğunuz burada bitiyor.'

  return `${step}${board.charAt(0).toUpperCase() + board.slice(1)}${alight ? `, ${alight}` : ''}${duration}.${more}`
}

export default function VoiceGuidance({
  legs,
  onClose,
}: {
  legs: VoiceGuidanceLeg[]
  onClose: () => void
}): ReactElement {
  const supported =
    typeof window !== 'undefined' && 'speechSynthesis' in window

  const steps = useMemo(
    () =>
      legs.map((leg, index) => ({
        sentence: legSentence(leg, index, legs.length),
        leg,
      })),
    [legs],
  )

  const [activeIndex, setActiveIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const utterancesRef = useRef<SpeechSynthesisUtterance[]>([])

  // Bilesen unmount olurken sesi kes
  useEffect(() => {
    if (!supported) return undefined

    return () => {
      window.speechSynthesis.cancel()
    }
  }, [supported])

  function speakFrom(index: number) {
    if (!supported || index < 0 || index >= steps.length) return

    window.speechSynthesis.cancel()
    utterancesRef.current = []

    // Aktif adimdan baslayarak kalan adimlari oku
    for (let i = index; i < steps.length; i++) {
      const utterance = new SpeechSynthesisUtterance(steps[i].sentence)
      utterance.lang = 'tr-TR'
      utterance.rate = 1

      utterance.onstart = () => setActiveIndex(i)

      if (i === steps.length - 1) {
        utterance.onend = () => setPlaying(false)
      }

      utterancesRef.current.push(utterance)
      window.speechSynthesis.speak(utterance)
    }

    setActiveIndex(index)
    setPlaying(true)
  }

  function handleStop() {
    if (!supported) return

    window.speechSynthesis.cancel()
    setPlaying(false)
  }

  function handleNext() {
    const next = Math.min(activeIndex + 1, steps.length - 1)
    speakFrom(next)
  }

  function handlePrev() {
    const prev = Math.max(activeIndex - 1, 0)
    speakFrom(prev)
  }

  return (
    <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-bold">🔊 Sesli rehberlik</p>
        <button
          type="button"
          onClick={onClose}
          aria-label="Sesli rehberliği kapat"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line text-muted transition-colors hover:border-accent hover:text-accent"
        >
          ✕
        </button>
      </div>

      {!supported ? (
        <p className="mt-3 text-sm text-muted">
          Bu cihaz sesli rehberliği desteklemiyor.
        </p>
      ) : (
        <>
          <div className="mt-3 flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={handlePrev}
              disabled={activeIndex === 0}
              aria-label="Önceki adım"
              className="flex h-11 w-11 items-center justify-center rounded-full border border-line bg-bg text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-40 disabled:hover:border-line disabled:hover:text-muted"
            >
              ⏮
            </button>
            <button
              type="button"
              onClick={() =>
                playing ? handleStop() : speakFrom(activeIndex)
              }
              aria-label={playing ? 'Durdur' : 'Oynat'}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-accent text-xl font-bold text-white shadow-lg shadow-accent/25 transition-transform hover:scale-105"
            >
              {playing ? '⏸' : '▶'}
            </button>
            <button
              type="button"
              onClick={handleNext}
              disabled={activeIndex >= steps.length - 1}
              aria-label="Sonraki adım"
              className="flex h-11 w-11 items-center justify-center rounded-full border border-line bg-bg text-muted transition-colors hover:border-accent hover:text-accent disabled:opacity-40 disabled:hover:border-line disabled:hover:text-muted"
            >
              ⏭
            </button>
          </div>

          <ol className="mt-4 space-y-2">
            {steps.map((step, index) => (
              <li
                key={index}
                className={`rounded-xl border px-3 py-2 text-sm transition-colors ${
                  index === activeIndex
                    ? 'border-accent/60 bg-accent/10 font-bold text-accent'
                    : 'border-line text-muted'
                }`}
              >
                {step.sentence}
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  )
}
