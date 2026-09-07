import { useEffect, useMemo, useState, type ReactElement } from 'react'
import type { Mode, PlanResult } from '@/lib/api'
import { isSaved, toggleSaved } from '@/lib/storage'
import { adsAvailable, removeBanner, showBottomBanner } from '@/lib/ads'
import {
  CarDetails,
  FlightDetails,
  isFerryRoute,
  isMetroRoute,
  isTramRoute,
  straightLineKm,
  TrainDetails,
  TransitList,
  WalkingDetails,
} from '@/components/RouteResults'
import {
  IconBus,
  IconCar,
  IconChevronRight,
  IconMoto,
  IconPlane,
  IconStar,
  IconTrain,
  IconWalk,
} from '@/icons'

const MODE_LABELS: Record<Mode, string> = {
  tumu: 'Tümü',
  otobus: 'Otobüs',
  metro: 'Metro',
  tramvay: 'Tramvay',
  deniz: 'Deniz',
  arac: 'Araba',
  motosiklet: 'Motosiklet',
  ucak: 'Uçak',
  tren: 'Tren',
  yuruyus: 'Yürüyüş',
}

type Candidate = {
  id: 'transit' | 'ucak' | 'tren' | 'arac' | 'yuruyus'
  title: string
  icon: (props: { className?: string }) => ReactElement
  minutes: number
  pricePerPerson: number | null
  total: number | null
  note?: string
}

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)

  if (hours === 0) return `${mins} dk`

  return `${hours} sa ${String(mins).padStart(2, '0')} dk`
}

function buildCandidates(plan: PlanResult, people: number, mode: Mode): Candidate[] {
  const candidates: Candidate[] = []
  const pt = plan.public_transport

  if (mode === 'yuruyus') {
    const distanceKm = plan.car?.distance_km ?? straightLineKm(plan) * 1.3

    candidates.push({
      id: 'yuruyus',
      title: 'Yürüyüş',
      icon: IconWalk,
      minutes: Math.round((distanceKm / 4.8) * 60),
      pricePerPerson: 0,
      total: 0,
      note: `~${distanceKm.toFixed(1)} km · tahmini`,
    })

    return candidates
  }

  if (pt.status === 'success' && pt.routes.length > 0) {
    const best =
      pt.recommendations?.fastest ?? pt.routes[0]

    const minutes = best.duration_minutes ?? 0
    const perPerson = best.fee

    candidates.push({
      id: 'transit',
      title: 'Toplu Taşıma',
      icon: IconBus,
      minutes,
      pricePerPerson: perPerson,
      total: perPerson != null ? perPerson * people : null,
      note: pt.source ? `${pt.source} verileriyle` : undefined,
    })
  }

  if (plan.flight?.available && plan.flight.duration_minutes != null) {
    candidates.push({
      id: 'ucak',
      title: 'Uçak',
      icon: IconPlane,
      minutes: plan.flight.duration_minutes,
      pricePerPerson: plan.flight.estimated_price_per_person ?? null,
      total: plan.flight.total_price ?? null,
      note: 'tahmini · havalimanı süreçleri dahil',
    })
  }

  if (plan.train?.available && plan.train.duration_minutes != null) {
    candidates.push({
      id: 'tren',
      title: 'Tren',
      icon: IconTrain,
      minutes: plan.train.duration_minutes,
      pricePerPerson: plan.train.estimated_price_per_person ?? null,
      total: plan.train.total_price ?? null,
      note: `${plan.train.distance_km} km · tahmini`,
    })
  }

  if (plan.car) {
    const isMoto = mode === 'motosiklet'

    candidates.push({
      id: 'arac',
      title: isMoto ? 'Motosiklet' : 'Araba',
      icon: isMoto ? IconMoto : IconCar,
      minutes: plan.car.duration_minutes,
      pricePerPerson: plan.car.cost_per_person,
      total: plan.car.total_cost,
      note: `${plan.car.distance_km} km · ${plan.car.vehicle}`,
    })
  }

  return candidates
}

function pickBest(candidates: Candidate[]): Candidate | null {
  if (candidates.length === 0) return null

  // Skor: dakika + TL/20 (1 dk ≈ 20 TL) — fiyat/süre dengesi
  let best = candidates[0]
  let bestScore = Number.POSITIVE_INFINITY

  for (const candidate of candidates) {
    const cost = candidate.total ?? candidate.pricePerPerson ?? 0
    const score = candidate.minutes + cost / 20

    if (score < bestScore) {
      bestScore = score
      best = candidate
    }
  }

  return best
}

function ModeCard({
  candidate,
  best,
  plan,
  people,
  listMode,
  routeIndex,
  onRouteIndexChange,
}: {
  candidate: Candidate
  best: Candidate | null
  plan: PlanResult
  people: number
  listMode: Mode
  routeIndex: number
  onRouteIndexChange: (index: number) => void
}) {
  const [open, setOpen] = useState(false)
  const Icon = candidate.icon
  const isBest = best?.id === candidate.id

  return (
    <div
      className={`rounded-2xl border bg-surface-2/90 ${
        isBest ? 'border-accent/60 shadow-lg shadow-accent/10' : 'border-line'
      }`}
    >
      <div className="p-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
            <Icon className="h-4.5 w-4.5" />
          </span>
          <div className="flex-1">
            <p className="text-sm font-bold">
              {candidate.title}
              {isBest && (
                <span className="ml-2 rounded-full bg-accent/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-accent">
                  En mantıklı
                </span>
              )}
            </p>
            {candidate.note && (
              <p className="break-words text-xs text-muted">{candidate.note}</p>
            )}
          </div>
        </div>

        <p className="mt-3 text-2xl font-bold tabular-nums">
          {formatDuration(candidate.minutes)}
        </p>

        <div className="mt-1 flex flex-wrap gap-x-3 text-sm text-muted">
          {candidate.pricePerPerson != null && (
            <span className="tabular-nums">
              ~{Math.round(candidate.pricePerPerson).toLocaleString('tr-TR')} TL / kişi
            </span>
          )}
          {candidate.total != null && people > 1 && (
            <span className="font-bold text-accent tabular-nums">
              ~{Math.round(candidate.total).toLocaleString('tr-TR')} TL toplam
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          aria-expanded={open}
          className="mt-3 flex w-full items-center justify-center gap-1 rounded-xl border border-line py-2 text-xs font-bold text-accent transition-colors hover:bg-accent/10"
        >
          {open ? 'GİZLE' : 'DETAYLAR'}
          <IconChevronRight
            className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-90' : ''}`}
          />
        </button>
      </div>

      {open && (
        <div className="border-t border-line px-4 py-4">
          {candidate.id === 'transit' && (
            <TransitList
              result={plan}
              mode={listMode}
              people={people}
              selectedIndex={routeIndex}
              onSelect={onRouteIndexChange}
            />
          )}
          {candidate.id === 'ucak' && plan.flight && (
            <FlightDetails flight={plan.flight} />
          )}
          {candidate.id === 'tren' && plan.train && (
            <TrainDetails train={plan.train} />
          )}
          {candidate.id === 'arac' && plan.car && (
            <CarDetails car={plan.car} people={people} />
          )}
          {candidate.id === 'yuruyus' && <WalkingDetails result={plan} />}
        </div>
      )}
    </div>
  )
}

export default function ResultsScreen({
  plan,
  people,
  mode,
  onBack,
  routeIndex,
  onRouteIndexChange,
}: {
  plan: PlanResult
  people: number
  mode: Mode
  onBack: () => void
  routeIndex: number
  onRouteIndexChange: (index: number) => void
}) {
  const candidates = useMemo(
    () => buildCandidates(plan, people, mode),
    [plan, people, mode],
  )

  // Seçili moda göre daralt: kullanıcı belirli bir tür seçtiyse
  // sonuç ekranı yalnızca o türü göstersin
  const modeCandidates = useMemo(() => {
    const routes = plan.public_transport.routes

    switch (mode) {
      case 'tumu':
        // Varsayilan: ozel arac haric butun secenekler
        return candidates.filter((candidate) => candidate.id !== 'arac')
      case 'otobus':
        return candidates.filter((candidate) => candidate.id === 'transit')
      case 'metro':
        return routes.some(isMetroRoute)
          ? candidates.filter((candidate) => candidate.id === 'transit')
          : []
      case 'tramvay':
        return routes.some(isTramRoute)
          ? candidates.filter((candidate) => candidate.id === 'transit')
          : []
      case 'deniz':
        return routes.some(isFerryRoute)
          ? candidates.filter((candidate) => candidate.id === 'transit')
          : []
      case 'motosiklet':
      case 'arac':
        return candidates.filter((candidate) => candidate.id === 'arac')
      case 'ucak':
        return candidates.filter((candidate) => candidate.id === 'ucak')
      case 'tren':
        return candidates.filter((candidate) => candidate.id === 'tren')
      case 'yuruyus':
        return candidates.filter((candidate) => candidate.id === 'yuruyus')
      default:
        return candidates
    }
  }, [candidates, mode, plan])

  const [showAll, setShowAll] = useState(false)
  useEffect(() => setShowAll(false), [plan, mode])

  // Sonuc ekraninda banner reklam: acilirken goster, kapanirken kaldir
  const withAds = useMemo(() => adsAvailable(), [])
  useEffect(() => {
    if (!withAds) return

    showBottomBanner()
    return () => {
      removeBanner()
    }
  }, [withAds])

  const visibleCandidates = showAll ? candidates : modeCandidates
  const best = useMemo(() => pickBest(visibleCandidates), [visibleCandidates])

  // Seçili modda sonuç yoksa net mesaj
  const modeEmptyMessage = (() => {
    if (visibleCandidates.length > 0) return null

    switch (mode) {
      case 'metro':
        return 'Bu iki nokta arasında metro ulaşımı bulunamadı.'
      case 'tramvay':
        return 'Bu iki nokta arasında tramvay hattı bulunamadı.'
      case 'deniz':
        return 'Bu iki nokta arasında deniz ulaşımı (vapur) bulunamadı.'
      case 'motosiklet':
        return plan.car_error ?? 'Motosiklet rotası hesaplanamadı.'
      case 'arac':
        return plan.car_error ?? 'Araba rotası hesaplanamadı.'
      case 'ucak':
        return plan.flight?.reason ?? 'Bu güzergah için uçak önerilmiyor.'
      case 'tren':
        return plan.train?.reason ?? 'Bu güzergah için tren önerilmiyor.'
      case 'yuruyus':
        return 'Yürüyüş mesafesi hesaplanamadı.'
      default:
        return plan.public_transport.error ?? 'Bu iki nokta arasında toplu taşıma rotası bulunamadı.'
    }
  })()

  // Seçili moda göre liste detay modu
  const listMode: Mode =
    mode === 'deniz' || mode === 'metro' || mode === 'tramvay' ? mode : 'otobus'

  const hasRailLeg = plan.public_transport.routes.some((route) =>
    route.legs.some(
      (leg) => leg.type !== 'walking' && /METRO|MARMARAY|TRAM|FUNIC|RAIL|NOSTAL/.test(leg.type.toUpperCase()),
    ),
  )

  // İETT verisi metro/tramvay/Marmaray içermez; kullanıcıya dürüstçe söyle
  const iettNote =
    plan.public_transport.status === 'success' &&
    (plan.public_transport.source ?? '').includes('İETT') &&
    !hasRailLeg

  const shortName = (place: string) =>
    place.split(',').slice(0, 1).join('').trim() || place

  const [saved, setSaved] = useState(() => isSaved(plan.start, plan.destination))

  function handleToggleSaved() {
    const nowSaved = toggleSaved({
      from: plan.start,
      to: plan.destination,
      people,
      mode,
    })
    setSaved(nowSaved)
  }

  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-bg">
      <div className={`mx-auto w-full max-w-xl px-4 pt-5 sm:px-6 ${withAds ? 'pb-32' : 'pb-10'}`}>
        <header className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            aria-label="Ana ekrana dön"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line bg-surface-2 text-muted transition-colors hover:border-accent hover:text-accent"
          >
            ←
          </button>
          <div className="min-w-0 flex-1 text-center">
            <p className="break-words text-sm font-bold">
              {shortName(plan.start)}
              <span className="mx-1.5 text-accent">→</span>
              {shortName(plan.destination)}
            </p>
            <p className="text-xs text-muted">{people} kişi</p>
          </div>
          <button
            type="button"
            onClick={handleToggleSaved}
            aria-label={saved ? 'Kayıtlılardan çıkar' : 'Kayıtlılara ekle'}
            aria-pressed={saved}
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border bg-surface-2 transition-colors ${
              saved
                ? 'border-accent text-accent'
                : 'border-line text-muted hover:border-accent hover:text-accent'
            }`}
          >
            <IconStar className={`h-4.5 w-4.5 ${saved ? 'fill-current' : ''}`} />
          </button>
        </header>

        {best && (
          <div className="mt-4 rounded-2xl border border-accent/40 bg-accent/10 px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-wide text-accent">
              🏆 En mantıklı seçenek
            </p>
            <p className="mt-1 text-sm">
              <b>{best.title}</b> — {formatDuration(best.minutes)}
              {best.total != null && (
                <>, ~{Math.round(best.total).toLocaleString('tr-TR')} TL</>
              )}
              . Fiyat/zaman açısından en dengeli seçenek.
            </p>
          </div>
        )}

        {iettNote && (
          <p className="mt-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-200">
            ℹ️ Bu sonuç İETT verisidir: otobüs, vapur ve dolmuş seçenekleri tamdır;
            metro, tramvay ve Marmaray hatları bu kaynakta yer almaz.
          </p>
        )}

        {modeEmptyMessage && (
          <div className="mt-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-4">
            <p className="text-sm text-amber-200">{modeEmptyMessage}</p>
            {candidates.length > 0 && !showAll && (
              <button
                type="button"
                onClick={() => setShowAll(true)}
                className="mt-2 text-xs font-bold text-accent underline-offset-2 hover:underline"
              >
                Tüm seçenekleri göster →
              </button>
            )}
          </div>
        )}

        {!modeEmptyMessage && visibleCandidates.length < candidates.length && (
          <p className="mt-4 flex items-center justify-between px-1 text-xs text-muted">
            <span>{MODE_LABELS[mode]} modunda sonuçlar</span>
            <button
              type="button"
              onClick={() => setShowAll((current) => !current)}
              className="font-bold text-accent underline-offset-2 hover:underline"
            >
              {showAll ? 'Sadece seçili mod' : 'Tümünü göster'}
            </button>
          </p>
        )}

        <div className="mt-4 space-y-3">
          {visibleCandidates.map((candidate) => (
            <ModeCard
              key={candidate.id}
              candidate={candidate}
              best={best}
              plan={plan}
              people={people}
              listMode={listMode}
              routeIndex={routeIndex}
              onRouteIndexChange={onRouteIndexChange}
            />
          ))}
        </div>

        <button
          type="button"
          onClick={onBack}
          className="mt-5 flex min-h-[48px] w-full items-center justify-center rounded-2xl border border-line bg-surface-2 font-bold text-muted transition-colors hover:border-accent hover:text-accent"
        >
          Yeni rota ara
        </button>
      </div>
    </div>
  )
}
