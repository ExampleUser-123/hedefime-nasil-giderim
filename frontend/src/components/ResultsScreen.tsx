import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactElement } from 'react'
import type { CarResult, Mode, PlanResult, TransitRoute } from '@/lib/api'
import { createShareRoute, reportFeedback } from '@/lib/api'
import { watchGetOff } from '@/lib/getOffAlert'
import VoiceGuidance from '@/components/VoiceGuidance'
import TripReport from '@/components/TripReport'
import LiveTripButton from '@/components/LiveTripButton'
import CrowdingCard from '@/components/CrowdingCard'
import { loadFavorites, toggleFavorite } from '@/lib/favorites'
import { adsAvailable, removeBanner, showBottomBanner } from '@/lib/ads'
import {
  CarDetails,
  FlightDetails,
  isFerryRoute,
  isMetroRoute,
  isTramRoute,
  LineClickContext,
  straightLineKm,
  TrainDetails,
  TransitList,
  WalkingDetails,
} from '@/components/RouteResults'
import LineDetailSheet from '@/components/LineDetailSheet'
import { extractCity } from '@/lib/cities'
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

// Mobil bottom sheet kademeleri (dvh): ozet bar / yari acik / tam ekran
const SNAP_H = { peek: 15, half: 52, full: 92 } as const
type SheetSnap = keyof typeof SNAP_H
const SNAP_ORDER: SheetSnap[] = ['peek', 'half', 'full']

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
  id: 'transit' | 'ucak' | 'tren' | 'arac' | 'moto' | 'yuruyus'
  title: string
  icon: (props: { className?: string }) => ReactElement
  minutes: number
  pricePerPerson: number | null
  total: number | null
  note?: string
  vehicleData?: CarResult
}

type SortMode = 'recommended' | 'least_walking' | 'least_transfers'

const SORT_LABELS: { id: SortMode; label: string }[] = [
  { id: 'recommended', label: 'Önerilen' },
  { id: 'least_walking', label: 'En az yürüme' },
  { id: 'least_transfers', label: 'En az aktarma' },
]

// Aktarma sayiminda yalnizca otobus/minibus/dolmus gecisleri say;
// rail/metro/tramvay/vapur sayilmaz.
function countBusTransfers(route: TransitRoute): number {
  return route.legs.filter((leg) => {
    const type = leg.type.toUpperCase()

    return type !== 'WALKING' && /BUS|MINIB|DOLMUS|DOLMUŞ|OTOB/.test(type)
  }).length
}

function sortTransitRoutes(routes: TransitRoute[], sortMode: SortMode): TransitRoute[] {
  if (sortMode === 'recommended') return routes

  const scored = routes.map((route, index) => ({
    route,
    index,
    key:
      sortMode === 'least_walking'
        ? route.walking_distance_m
        : countBusTransfers(route),
  }))

  // Stabil siralama: esit degerlerde mevcut sira korunur
  scored.sort((a, b) => a.key - b.key || a.index - b.index)

  return scored.map((item) => item.route)
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

  const pushVehicle = (data: CarResult) => {
    const isMoto = data.vehicle_type === 'motosiklet'

    candidates.push({
      id: isMoto ? 'moto' : 'arac',
      title: isMoto ? 'Motosiklet' : 'Araba',
      icon: isMoto ? IconMoto : IconCar,
      minutes: data.duration_minutes,
      pricePerPerson: data.cost_per_person,
      total: data.total_cost,
      note: `${data.distance_km} km · ${data.vehicle}`,
      vehicleData: data,
    })
  }

  if (plan.car) pushVehicle(plan.car)
  if (plan.other_vehicle) pushVehicle(plan.other_vehicle)

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
            <FlightDetails flight={plan.flight} from={plan.start} to={plan.destination} />
          )}
          {candidate.id === 'tren' && plan.train && (
            <TrainDetails train={plan.train} from={plan.start} to={plan.destination} />
          )}
          {candidate.vehicleData && (
            <CarDetails car={candidate.vehicleData} people={people} />
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
  onRequireLogin,
}: {
  plan: PlanResult
  people: number
  mode: Mode
  onBack: () => void
  routeIndex: number
  onRouteIndexChange: (index: number) => void
  onRequireLogin: () => void
}) {
  const candidates = useMemo(
    () => buildCandidates(plan, people, mode),
    [plan, people, mode],
  )

  // Rota siralama/filtre cipleri: varsayilan 'Onerilen' mevcut sirayi korur
  const [sortMode, setSortMode] = useState<SortMode>('recommended')
  const hasTransitRoutes = plan.public_transport.routes.length > 0

  const sortedPlan = useMemo<PlanResult>(() => {
    if (sortMode === 'recommended') return plan

    return {
      ...plan,
      public_transport: {
        ...plan.public_transport,
        routes: sortTransitRoutes(plan.public_transport.routes, sortMode),
      },
    }
  }, [plan, sortMode])

  // Sesli rehber: secili rota (yoksa ilk rota)
  const selectedRoute =
    plan.public_transport.routes[routeIndex] ?? plan.public_transport.routes[0] ?? null

  const [showVoice, setShowVoice] = useState(false)
  useEffect(() => setShowVoice(false), [plan])

  // Hat detay sayfasi: rota adimlarindaki hat adina dokununca acilir
  const [lineSheet, setLineSheet] = useState<{ city: string; line: string; stops?: string[]; name?: string } | null>(null)
  useEffect(() => {
    setLineSheet(null)
    setSnap('peek')
  }, [plan])

  // 3 kademeli bottom sheet (mobil) + sol panel (masaustu).
  // Masaustunde (sm+) panel her zaman tam boy solda; snap yalnizca mobilde gecerli.
  const [snap, setSnap] = useState<SheetSnap>('peek')
  const [sheetH, setSheetH] = useState<number>(SNAP_H.peek)
  const [dragging, setDragging] = useState(false)
  const [isDesktop, setIsDesktop] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 640px)').matches,
  )
  useEffect(() => {
    const query = window.matchMedia('(min-width: 640px)')
    const update = () => setIsDesktop(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  useEffect(() => {
    if (!dragging) setSheetH(SNAP_H[snap])
  }, [snap, dragging])
  const gripStart = useRef<{ y: number; h: number } | null>(null)
  const gripMoved = useRef(false)
  const sheetHRef = useRef<number>(SNAP_H.peek)
  sheetHRef.current = sheetH

  function onGripDown(e: ReactPointerEvent<HTMLDivElement>) {
    gripStart.current = { y: e.clientY, h: sheetH }
    gripMoved.current = false
    setDragging(true)
  }
  function onGripMove(e: ReactPointerEvent<HTMLDivElement>) {
    const start = gripStart.current
    if (!start) return
    if (Math.abs(e.clientY - start.y) > 6) gripMoved.current = true
    const delta = ((start.y - e.clientY) / window.innerHeight) * 100
    setSheetH(Math.min(SNAP_H.full, Math.max(12, start.h + delta)))
  }
  function onGripUp() {
    if (!gripStart.current) return
    gripStart.current = null
    setDragging(false)
    const h = sheetHRef.current
    let nearest: SheetSnap = 'peek'
    let gap = Infinity
    for (const key of SNAP_ORDER) {
      const d = Math.abs(SNAP_H[key] - h)
      if (d < gap) {
        gap = d
        nearest = key
      }
    }
    setSnap(nearest)
    setSheetH(SNAP_H[nearest])
  }
  function onGripClick() {
    if (gripMoved.current) {
      gripMoved.current = false
      return
    }
    setSnap((s) => SNAP_ORDER[(SNAP_ORDER.indexOf(s) + 1) % SNAP_ORDER.length])
  }

  // Sehir adi gelmezse baslangic noktasindan turet (bilinen sehir listesiyle)
  const fallbackCity = extractCity(plan.start)

  // --- İnme uyarisi: hedef duraga GPS ile yaklasma takibi ---
  const [offState, setOffState] = useState<'off' | 'watching' | 'arrived'>('off')
  const [offDistance, setOffDistance] = useState<number | null>(null)
  const [offError, setOffError] = useState<string | null>(null)
  const stopWatchRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    // yeni aramada eski izlemeyi temizle
    stopWatchRef.current?.()
    stopWatchRef.current = null
    setOffState('off')
    setOffDistance(null)
    setOffError(null)
    return () => {
      stopWatchRef.current?.()
      stopWatchRef.current = null
    }
  }, [plan])

  const toggleGetOffAlert = () => {
    if (offState === 'watching') {
      stopWatchRef.current?.()
      stopWatchRef.current = null
      setOffState('off')
      setOffDistance(null)
      return
    }

    setOffError(null)
    setOffDistance(null)
    setOffState('watching')

    watchGetOff(plan.end_coord, plan.destination, {
      onDistance: (m) => setOffDistance(m),
      onArrived: () => {
        stopWatchRef.current?.()
        stopWatchRef.current = null
        setOffState('arrived')
      },
      onError: (msg) => {
        stopWatchRef.current?.()
        stopWatchRef.current = null
        setOffState('off')
        setOffError(msg)
      },
    })
      .then((stop) => {
        stopWatchRef.current = stop
      })
      .catch(() => {
        setOffState('off')
        setOffError('İnme uyarısı başlatılamadı.')
      })
  }

  // --- Bu bilgi yanlis raporu ---
  const [showReport, setShowReport] = useState(false)
  const [reportText, setReportText] = useState('')
  const [reportState, setReportState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle')

  const submitReport = async () => {
    if (!reportText.trim() || reportState === 'sending') return
    setReportState('sending')
    try {
      await reportFeedback({
        message: reportText.trim(),
        context: `${plan.start} → ${plan.destination} (${MODE_LABELS[mode]})`,
      })
      setReportState('done')
      setReportText('')
      setTimeout(() => {
        setShowReport(false)
        setReportState('idle')
      }, 2200)
    } catch {
      setReportState('error')
    }
  }

  // Seçili moda göre daralt: kullanıcı belirli bir tür seçtiyse
  // sonuç ekranı yalnızca o türü göstersin
  const modeCandidates = useMemo(() => {
    const routes = plan.public_transport.routes

    switch (mode) {
      case 'tumu':
        // Varsayilan: ozel arac/motosiklet haric butun secenekler
        return candidates.filter(
          (candidate) => candidate.id !== 'arac' && candidate.id !== 'moto',
        )
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
        return candidates.filter((candidate) => candidate.id === 'moto')
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

  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  // Doluluk bildirimi: secili rotanin otobus/minibus hatlari
  const busLines = [...new Set(
    (selectedRoute?.legs ?? [])
      .filter((leg) => {
        const t = leg.type.toUpperCase()
        return t !== 'WALKING' && /BUS|MINIB|DOLMUS|DOLMUŞ|OTOB/.test(t)
      })
      .map((leg) => leg.line)
      .filter((line): line is string => !!line),
  )].slice(0, 3)
  const routeCity = plan.start.split(',').pop()?.trim() ?? ''

  // Bu guzergah hesap favorilerinde var mi?
  useEffect(() => {
    let cancelled = false

    loadFavorites()
      .then(({ items }) => {
        if (cancelled) return
        setSaved(items.some((item) => item.from === plan.start && item.to === plan.destination))
      })
      .catch(() => {
        // sunucu yoksa yildiz kapali kalir
      })

    return () => {
      cancelled = true
    }
  }, [plan.start, plan.destination])

  async function handleToggleSaved() {
    if (saving) return

    setSaving(true)

    try {
      const result = await toggleFavorite({
        from: plan.start,
        to: plan.destination,
        people,
        mode,
      })

      if (result.needsLogin) {
        onRequireLogin()
        return
      }

      setSaved(result.saved)
    } catch {
      // hata durumunda yildiz durumunu dokunma
    } finally {
      setSaving(false)
    }
  }

  const [shared, setShared] = useState(false)

  async function handleShare() {
    const lines = visibleCandidates
      .filter((option) => option.minutes > 0)
      .slice(0, 3)
      .map((option) => {
        const cost = option.total != null
          ? ` ~${Math.round(option.total).toLocaleString('tr-TR')} TL`
          : ''
        const time = option.minutes >= 60
          ? `${Math.floor(option.minutes / 60)}s ${option.minutes % 60}dk`
          : `${option.minutes}dk`
        return `• ${option.title}: ${time}${cost}`
      })

    // Paylasim linki olustur; olusmazsa metin ozeti yine de paylasilir
    let url: string | null = null
    try {
      const res = await createShareRoute({
        start: plan.start,
        destination: plan.destination,
        people,
        mode,
      })
      url = res.url
    } catch {
      // link servisleri yoksa metin ozetiyle devam
    }

    const text = [
      `${shortName(plan.start)} → ${shortName(plan.destination)} (${people} kişi)`,
      ...lines,
      ...(url ? ['', url] : []),
      url ? '' : 'Hedefime Nasıl Giderim ile hesaplandı',
    ].join('\n')

    try {
      if (typeof navigator !== 'undefined' && navigator.share) {
        await navigator.share({ title: 'Rota', text })
      } else {
        await navigator.clipboard.writeText(text)
        setShared(true)
        setTimeout(() => setShared(false), 2000)
      }
    } catch {
      // kullanici paylasimi iptal ettiyse sessiz gec
    }
  }

  return (
    <LineClickContext.Provider value={(city, line, stops, name) => setLineSheet({ city: city || fallbackCity, line, stops, name })}>
      {/* Seffaf kok: harita her zaman gorunur ve dokunulabilir.
          Mobil: 3 kademeli bottom sheet. Masaustu (sm+): sol yan panel. */}
      <div className="pointer-events-none fixed inset-0 z-40">
      <section
        className={`sheet-enter pointer-events-auto absolute inset-x-0 bottom-0 mx-auto flex w-full max-w-xl flex-col overflow-hidden rounded-t-3xl border-x border-t border-line bg-bg shadow-2xl shadow-black/60 sm:bottom-0 sm:left-0 sm:right-auto sm:top-0 sm:mx-0 sm:h-full sm:w-[380px] sm:max-w-none sm:rounded-none sm:border-x-0 sm:border-y-0 sm:border-r sm:shadow-black/40 ${dragging ? '' : 'transition-[height] duration-300 ease-out'}`}
        style={isDesktop ? undefined : { height: `${sheetH}dvh` }}
        role="dialog"
        aria-label="Rota sonuçları"
      >
      {!isDesktop && (
      <div className="relative shrink-0 select-none pb-1 pt-2.5">
        <div
          className="cursor-grab touch-none active:cursor-grabbing"
          onPointerDown={onGripDown}
          onPointerMove={onGripMove}
          onPointerUp={onGripUp}
          onPointerCancel={onGripUp}
          onClick={onGripClick}
          role="button"
          aria-label={snap === 'full' ? 'Paneli küçült' : 'Paneli büyüt'}
        >
          <div className="mx-auto h-1.5 w-12 rounded-full bg-line" aria-hidden="true" />
        </div>
        {snap !== 'peek' && (
          <button
            type="button"
            onClick={() => setSnap('peek')}
            aria-label="Paneli alta küçült, haritaya dön"
            className="absolute right-3 top-1.5 flex h-8 w-8 items-center justify-center rounded-full border border-line bg-surface-2 text-sm text-muted transition-colors hover:border-accent hover:text-accent"
          >
            🗺
          </button>
        )}
      </div>
      )}
      {!isDesktop && snap === 'peek' ? (
        <button
          type="button"
          onClick={() => setSnap('half')}
          aria-label="Rota detaylarını aç"
          className="flex min-h-0 flex-1 items-center gap-3 px-4 pb-[env(safe-area-inset-bottom)] text-left"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/15 text-base">
            🧭
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-bold">
              {best ? best.title : shortName(plan.start)}
              {best && (
                <span className="font-normal text-muted"> — {formatDuration(best.minutes)}</span>
              )}
            </span>
            <span className="block text-xs text-muted tabular-nums">
              {best?.total != null
                ? `~${Math.round(best.total).toLocaleString('tr-TR')} TL`
                : `${people} kişi`}
              {' · '}Detaylar ↑
            </span>
          </span>
        </button>
      ) : (
      <div className={`min-h-0 flex-1 overflow-y-auto px-4 sm:px-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden ${withAds ? 'pb-32' : 'pb-10'}`}>
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
            onClick={handleShare}
            aria-label="Rotayı paylaş"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line bg-surface-2 text-muted transition-colors hover:border-accent hover:text-accent"
          >
            {shared ? '✓' : <svg viewBox="0 0 24 24" className="h-4.5 w-4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>}
          </button>
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

        <div className="mt-3">
          <LiveTripButton plan={plan} onRequireLogin={onRequireLogin} />
        </div>

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

        {hasTransitRoutes && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {SORT_LABELS.map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => setSortMode(option.id)}
                aria-pressed={sortMode === option.id}
                className={`rounded-full border px-3 py-1.5 text-xs font-bold transition-colors ${
                  sortMode === option.id
                    ? 'border-accent bg-accent/15 text-accent'
                    : 'border-line bg-surface-2 text-muted hover:border-accent hover:text-accent'
                }`}
              >
                {option.label}
              </button>
            ))}
            <button
              type="button"
              onClick={toggleGetOffAlert}
              aria-pressed={offState !== 'off'}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-bold transition-colors ${
                offState !== 'off'
                  ? 'border-accent bg-accent/15 text-accent'
                  : 'border-line bg-surface-2 text-accent hover:border-accent'
              } ${offState === 'arrived' ? 'ml-auto' : ''}`}
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
              {offState === 'watching' ? 'İzleniyor…' : offState === 'arrived' ? 'İnme zamanı!' : 'İnme uyarısı'}
            </button>
            <button
              type="button"
              onClick={() => setShowVoice(true)}
              aria-label="Sesli rehber"
              className="ml-auto flex items-center gap-1.5 rounded-full border border-line bg-surface-2 px-3 py-1.5 text-xs font-bold text-accent transition-colors hover:border-accent"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="currentColor" stroke="none" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
              </svg>
              Sesli rehber
            </button>
          </div>
        )}

        {offState === 'watching' && offDistance != null && (
          <p className="mt-2 text-xs font-bold text-accent">
            🚏 {plan.destination} durağına ~{Math.round(offDistance / 10) * 10} m — yaklaştıkça haber vereceğiz
          </p>
        )}
        {offState === 'arrived' && (
          <p className="mt-2 text-xs font-bold text-accent">
            🔔 İnme zamanı! {plan.destination} durağına ulaştın.
          </p>
        )}
        {offError && <p className="mt-2 text-xs text-red-300">{offError}</p>}

        <div className="mt-4 space-y-3">
          {visibleCandidates.map((candidate) => (
            <ModeCard
              key={candidate.id}
              candidate={candidate}
              best={best}
              plan={sortedPlan}
              people={people}
              listMode={listMode}
              routeIndex={routeIndex}
              onRouteIndexChange={onRouteIndexChange}
            />
          ))}
        </div>

        {!hasTransitRoutes && (
          <div className="mt-4 rounded-2xl border border-line bg-surface-2 px-4 py-3">
            <p className="text-xs font-bold text-accent">🚐 Dolmuş / minibüs seçeneği</p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              Aradığın güzergahta dolmuş veya minibüs hattı olabilir — bu hatların saat verisi
              uygulamamızda ayrıntılı değil. AI asistanına “{plan.start} → {plan.destination} dolmuş ile
              nasıl gidilir, ücreti ne kadar?” diye sor; güzergah, aktarma ve tahmini ücreti senin için
              araştırır.
            </p>
          </div>
        )}

        {(() => {
          // TripReport: secili toplu tasima rotasindan; yoksa en mantikli secenekten
          const from = plan.start
          const to = plan.destination

          if (selectedRoute) {
            const walkingM = selectedRoute.walking_distance_m ?? 0
            const costPerPerson = selectedRoute.fee
            const legsCount = selectedRoute.legs.filter((leg) => leg.type !== 'walking').length || 1

            return (
              <TripReport
                from={from}
                to={to}
                people={people}
                totalMinutes={selectedRoute.duration_minutes ?? best?.minutes ?? 0}
                walkingDistanceM={walkingM}
                costPerPerson={costPerPerson ?? 0}
                totalCost={costPerPerson != null ? costPerPerson * people : best?.total ?? 0}
                legsCount={legsCount}
              />
            )
          }

          if (best) {
            return (
              <TripReport
                from={from}
                to={to}
                people={people}
                totalMinutes={best.minutes}
                walkingDistanceM={0}
                costPerPerson={best.pricePerPerson ?? 0}
                totalCost={best.total ?? (best.pricePerPerson != null ? best.pricePerPerson * people : 0)}
                legsCount={1}
              />
            )
          }

          return null
        })()}

        {busLines.length > 0 && routeCity && (
          <CrowdingCard city={routeCity} lines={busLines} />
        )}

        <button
          type="button"
          onClick={() => setShowReport(true)}
          className="mt-4 flex min-h-[40px] w-full items-center justify-center gap-1.5 rounded-2xl border border-line bg-transparent text-xs font-bold text-muted transition-colors hover:border-accent hover:text-accent"
        >
          ⚠ Bu bilgi yanlış mı? Bildir
        </button>

        <button
          type="button"
          onClick={onBack}
          className="mt-2 flex min-h-[48px] w-full items-center justify-center rounded-2xl border border-line bg-surface-2 font-bold text-muted transition-colors hover:border-accent hover:text-accent"
        >
          Yeni rota ara
        </button>
      </div>
      )}

      {showReport && (
        <div className="pointer-events-auto fixed inset-0 z-50 flex items-end justify-center bg-black/60 sm:items-center" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-t-3xl border border-line bg-surface p-5 sm:rounded-3xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-extrabold">Bu bilgi yanlış mı?</h3>
              <button
                type="button"
                onClick={() => { setShowReport(false); setReportState('idle') }}
                aria-label="Kapat"
                className="rounded-full p-1.5 text-muted hover:text-text"
              >
                ✕
              </button>
            </div>
            {reportState === 'done' ? (
              <p className="mt-4 text-sm text-accent">Teşekkürler! Bildirimin ekibe iletildi — kontrol edip verileri güncelleyeceğiz.</p>
            ) : (
              <>
                <p className="mt-1 text-xs text-muted">
                  Yanlış saat, eksik hat veya rota hatası bulduysan yaz; verilerimizi bu bildirimlerle düzeltiyoruz.
                </p>
                <textarea
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  rows={4}
                  maxLength={500}
                  placeholder="Örn: 640 hattı hafta sonu hiç geçmiyor / saatler yanlış…"
                  className="mt-3 w-full rounded-2xl border border-line bg-surface-2 px-4 py-3 text-sm text-text placeholder:text-muted/60 focus:border-accent focus:outline-none"
                />
                {reportState === 'error' && (
                  <p className="mt-2 text-xs text-red-300">Gönderilemedi — bağlantını kontrol edip tekrar dene.</p>
                )}
                <button
                  type="button"
                  onClick={submitReport}
                  disabled={!reportText.trim() || reportState === 'sending'}
                  className="mt-3 flex min-h-[46px] w-full items-center justify-center rounded-2xl bg-accent font-extrabold text-[#04241d] transition-opacity disabled:opacity-40"
                >
                  {reportState === 'sending' ? 'Gönderiliyor…' : 'Bildirimi gönder'}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {showVoice && selectedRoute && (
        <VoiceGuidance
          legs={selectedRoute.legs.map((leg) => ({
            type: leg.type,
            name: leg.name,
            line: leg.line,
            from_stop: leg.from_stop,
            to_stop: leg.to_stop,
            distance_m: leg.distance_m,
          }))}
          onClose={() => setShowVoice(false)}
        />
      )}

      {lineSheet && (
        <div className="pointer-events-auto">
        <LineDetailSheet
          city={lineSheet.city}
          line={lineSheet.line}
          lat={plan.start_coord.lat}
          lon={plan.start_coord.lon}
          fallbackStops={lineSheet.stops}
          fallbackName={lineSheet.name}
          onClose={() => setLineSheet(null)}
        />
        </div>
      )}
      </section>
      </div>
    </LineClickContext.Provider>
  )
}
