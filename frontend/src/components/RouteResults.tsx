import { createContext, useContext, useEffect, useState, type ReactElement } from 'react'
import { DepartureBadge, DepartureCityContext, fetchDepartureList } from '@/components/DepartureBadge'
import type { NextDeparture } from '@/lib/api'
import { extractCity } from '@/lib/cities'
import { openInApp, TCDD_URL } from '@/lib/navigate'
import type { CarResult, FlightEstimate, LatLng, Mode, PlanResult, TrainEstimate, TransitLeg, TransitRoute } from '@/lib/api'
import {
  IconBus,
  IconCar,
  IconChevronRight,
  IconClock,
  IconFerry,
  IconMetro,
  IconPlane,
  IconRoute,
  IconTrain,
  IconWallet,
  IconWalk,
} from '@/icons'

type Recommendations = PlanResult['recommendations']

// Hat detay sayfasini acan callback; ResultsScreen saglar (hat rozetlerine dokunma)
// stops: hattin bu rotadaki durak adlari (backend'te hat bulunamazsa yedek)
// coords: hattin bu rotadaki geometrisi (haritada vurgu icin)
export const LineClickContext = createContext<(city: string, line: string, stops?: string[], name?: string, coords?: LatLng[]) => void>(() => {})

function routeKey(route: TransitRoute): string {
  return JSON.stringify([
    route.fee,
    route.walking_distance_m,
    route.departure_time,
    route.arrival_time,
    route.legs.map((leg) => [leg.type, leg.line, leg.route_id]),
  ])
}

function getBadges(route: TransitRoute, recommendations: Recommendations): string[] {
  const key = routeKey(route)
  const badges: string[] = []

  if (recommendations.fastest && routeKey(recommendations.fastest) === key) badges.push('En Hızlı')
  if (recommendations.cheapest && routeKey(recommendations.cheapest) === key) badges.push('En Ucuz')
  if (recommendations.least_walking && routeKey(recommendations.least_walking) === key) badges.push('En Az Yürüyüş')

  return badges
}

function legIcon(leg: TransitLeg) {
  if (leg.type === 'walking') return IconWalk

  const type = leg.type.toUpperCase()

  if (/METRO|MARMARAY|TRAM|FUNIC|CABLE|NOSTAL/.test(type)) return IconMetro

  if (/FERRY|VAPUR|TURYOL|SHAT|SEHIR_HATLARI/.test(type)) return IconFerry

  return IconBus
}

function straightLineKm(result: PlanResult): number {
  const R = 6371
  const toRad = (deg: number) => (deg * Math.PI) / 180

  const dLat = toRad(result.end_coord.lat - result.start_coord.lat)
  const dLon = toRad(result.end_coord.lon - result.start_coord.lon)

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(result.start_coord.lat)) *
      Math.cos(toRad(result.end_coord.lat)) *
      Math.sin(dLon / 2) ** 2

  return 2 * R * Math.asin(Math.sqrt(a))
}

export { straightLineKm }

export function CarDetails({ car, people }: { car: CarResult; people: number }) {
  return (
    <div>
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <IconCar className="h-5 w-5" />
        </span>
        <div>
          <p className="text-sm font-bold">Arabayla</p>
          <p className="text-xs text-muted">{car.vehicle}</p>
        </div>
        <span className="ml-auto rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent">
          {car.duration_minutes} dk
        </span>
      </div>

      <dl className="mt-3.5 grid grid-cols-2 gap-2 text-sm">
        <div className="rounded-xl border border-line bg-bg/50 px-3.5 py-2.5">
          <dt className="text-xs text-muted">Mesafe</dt>
          <dd className="mt-0.5 font-semibold tabular-nums">{car.distance_km} km</dd>
        </div>
        <div className="rounded-xl border border-line bg-bg/50 px-3.5 py-2.5">
          <dt className="text-xs text-muted">Yakıt</dt>
          <dd className="mt-0.5 font-semibold tabular-nums">{car.fuel_liters} L</dd>
        </div>
        <div className="rounded-xl border border-line bg-bg/50 px-3.5 py-2.5">
          <dt className="text-xs text-muted">Toplam maliyet</dt>
          <dd className="mt-0.5 font-semibold tabular-nums">{car.total_cost} TL</dd>
        </div>
        <div className="rounded-xl border border-line bg-bg/50 px-3.5 py-2.5">
          <dt className="text-xs text-muted">Kişi başı ({people} kişi)</dt>
          <dd className="mt-0.5 font-semibold tabular-nums text-accent">{car.cost_per_person} TL</dd>
        </div>
      </dl>
    </div>
  )
}

export function WalkingDetails({ result }: { result: PlanResult }) {
  const distanceKm = (result.car?.distance_km ?? straightLineKm(result) * 1.3)
  const minutes = Math.round((distanceKm / 4.8) * 60)

  return (
    <div>
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <IconWalk className="h-5 w-5" />
        </span>
        <div>
          <p className="text-sm font-bold">Yürüyerek</p>
          <p className="text-xs text-muted">Tahmini süre, rota uzunluğuna göre hesaplandı</p>
        </div>
        <span className="ml-auto rounded-full bg-accent/15 px-2.5 py-1 text-xs font-bold text-accent">
          ~{minutes} dk
        </span>
      </div>

      <div className="mt-3.5 rounded-xl border border-line bg-bg/50 px-3.5 py-2.5 text-sm">
        <p className="font-semibold tabular-nums">~{distanceKm.toFixed(1)} km yürüme</p>
        {distanceKm > 10 && (
          <p className="mt-1 text-xs text-amber-300/90">
            Bu mesafe yürümek için oldukça uzun; toplu taşıma veya araç daha uygun olabilir.
          </p>
        )}
      </div>
    </div>
  )
}

// Yaklaşan sefer rozeti icin leg anahtari (hat + binis duragi)
function departureLegKey(leg: TransitLeg): string {
  return `${leg.line ?? ''}|${leg.from_stop ?? ''}`
}

// Görünen rotalardaki ilk `limit` adet bus leg'in anahtarini dondurur.
function firstBusLegKeys(routes: TransitRoute[], limit = 3): Set<string> {
  const keys = new Set<string>()

  for (const route of routes) {
    for (const leg of route.legs) {
      if (leg.type === 'bus' && keys.size < limit) {
        keys.add(departureLegKey(leg))
      }
    }
  }

  return keys
}

// "HH:MM" -> dakika. Gecersizse null.
function parseHM(time: string | null | undefined): number | null {
  if (!time) return null
  const match = /^(\d{1,2}):(\d{2})/.exec(time.trim())
  if (!match) return null
  const h = Number(match[1])
  const m = Number(match[2])
  if (h > 23 || m > 59) return null
  return h * 60 + m
}

// Arac ici net sure (dk). Gece yarisi gecisini tolere eder.
function legRideMinutes(departure: string | null, arrival: string | null): number | null {
  const d = parseHM(departure)
  const a = parseHM(arrival)
  if (d == null || a == null) return null
  let diff = a - d
  if (diff < 0) diff += 24 * 60
  return diff
}

// Hatin sonraki 3 kalkisi (zaman cizelgesi). Veri yoksa hicbir sey cizmez.
function LegTimetable({
  line,
  stop,
  lat,
  lon,
}: {
  line: string | null
  stop: string | null
  lat?: number
  lon?: number
}) {
  const city = useContext(DepartureCityContext)
  const [times, setTimes] = useState<NextDeparture[] | null>(null)

  useEffect(() => {
    if (!city || !line || !stop) return
    let alive = true
    fetchDepartureList(city, line, stop, lat, lon)
      .then((departures) => {
        if (alive) setTimes(departures?.slice(0, 3) ?? [])
      })
      .catch(() => {
        if (alive) setTimes([])
      })
    return () => {
      alive = false
    }
  }, [city, line, stop, lat, lon])

  if (!times || times.length === 0) return null

  // Sefer sikligi: kalkis araliklarinin ortancasi (yaklasik)
  let frequency: number | null = null
  if (times.length >= 2) {
    const mins = times
      .map((d) => parseHM(d.time))
      .filter((m): m is number => m != null)
    const gaps: number[] = []
    for (let i = 1; i < mins.length; i++) {
      let gap = mins[i] - mins[i - 1]
      if (gap <= 0) gap += 24 * 60
      gaps.push(gap)
    }
    if (gaps.length > 0) {
      gaps.sort((a, b) => a - b)
      frequency = gaps[Math.floor(gaps.length / 2)]
    }
  }

  return (
    <div className="mt-1 text-[11px] text-muted tabular-nums">
      <p>
        Sonraki seferler: {times.map((d) => d.time).join(', ')}
        {times[0]?.source === 'tahmini' && ' (tahmini)'}
      </p>
      {frequency != null && frequency > 0 && (
        <p>~her {frequency} dk'da bir kalkar (yaklaşık)</p>
      )}
    </div>
  )
}

function LegRow({
  leg,
  showDeparture,
  lat,
  lon,
  step,
}: {
  leg: TransitLeg
  showDeparture?: boolean
  lat?: number
  lon?: number
  /** Adim numarasi (1'den baslar); verilirse "N. Adim" rozeti cizer */
  step?: number
}) {
  const Icon = legIcon(leg)

  const stepBadge = step != null && (
    <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 px-1 text-[10px] font-bold text-accent tabular-nums" aria-label={`${step}. adım`}>
      {step}
    </span>
  )

  if (leg.type === 'walking') {
    // Sehir ici yürüme hizi ~70 m/dk (tahmini).
    const walkMin = leg.distance_m ? Math.max(1, Math.round(leg.distance_m / 70)) : null
    const streets = (leg.streets ?? []).filter(Boolean)
    return (
      <li className="flex items-center gap-2 py-2">
        {stepBadge}
        <Icon className="h-4 w-4 shrink-0 text-muted" />
        <div className="min-w-0">
          <p className="text-sm text-muted">
            {leg.distance_m ? `${Math.round(leg.distance_m)} m yürü` : 'Yürü'}
            {walkMin != null && ` (~${walkMin} dk, tahmini)`}
            <span className="mx-1.5 text-line" aria-hidden="true">·</span>
            {leg.from_stop ?? ''}
            {leg.to_stop && ` → ${leg.to_stop}`}
          </p>
          {streets.length > 0 && (
            <p className="mt-0.5 break-words text-[11px] text-muted">
              🧭 {streets.join(' → ')} üzerinden
            </p>
          )}
        </div>
      </li>
    )
  }

  const rideMin = legRideMinutes(leg.departure_time, leg.arrival_time)
  const stopCount = leg.stops.length > 1 ? leg.stops.length - 1 : null

  return (
    <li className="flex items-start gap-2 py-2">
      {stepBadge}
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
      <div className="min-w-0 flex-1">
        <LineTitle leg={leg} showDeparture={showDeparture} lat={lat} lon={lon} />
        {showDeparture && (
          <LegTimetable line={leg.line} stop={leg.from_stop} lat={lat} lon={lon} />
        )}
        {leg.alternate_lines.length > 0 && (
          <span className="text-xs font-normal text-muted">(+{leg.alternate_lines.length} alternatif)</span>
        )}
        <p className="mt-0.5 break-words text-xs text-muted">
          {leg.from_stop} → {leg.to_stop}
          {leg.departure_time && ` · ${leg.departure_time}`}
          {leg.arrival_time && ` – ${leg.arrival_time}`}
          {stopCount != null && ` · ${stopCount} durak`}
          {rideMin != null && ` · araçta ~${rideMin} dk`}
        </p>
      </div>
    </li>
  )
}

function LineTitle({
  leg,
  showDeparture,
  lat,
  lon,
}: {
  leg: TransitLeg
  showDeparture?: boolean
  lat?: number
  lon?: number
}) {
  const onLineClick = useContext(LineClickContext)
  const city = useContext(DepartureCityContext)
  const line = leg.line
  const label = leg.name ?? leg.line ?? 'Hat'

  if (!line || !onLineClick) {
    return (
      <p className="flex flex-wrap items-center gap-1.5 text-sm font-semibold">
        {label}
        {showDeparture && (
          <DepartureBadge line={leg.line} stop={leg.from_stop} lat={lat} lon={lon} />
        )}
      </p>
    )
  }

  return (
    <p className="flex flex-wrap items-center gap-1.5 text-sm font-semibold">
      <button
        type="button"
        onClick={() => onLineClick(city, line, leg.stops, leg.name ?? undefined, leg.coords)}
        className="break-words text-left font-semibold text-accent underline decoration-accent/40 underline-offset-2 transition-colors hover:decoration-accent"
      >
        {label}
      </button>
      {showDeparture && (
        <DepartureBadge line={leg.line} stop={leg.from_stop} lat={lat} lon={lon} />
      )}
    </p>
  )
}

function TransitRouteCard({
  route,
  people,
  badges,
  selected,
  onSelect,
  departureLegs,
  lat,
  lon,
}: {
  route: TransitRoute
  people: number
  badges: string[]
  selected: boolean
  onSelect: () => void
  departureLegs?: Set<string>
  lat?: number
  lon?: number
}) {
  const totalPrice = route.fee != null ? route.fee * people : null

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-bg/50">
      <button
        type="button"
        onClick={onSelect}
        aria-expanded={selected}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-surface-2/60"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-base font-bold tabular-nums">{route.duration_minutes ?? '?'} dk</span>
            {totalPrice != null && (
              <span className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums">
                {people > 1 ? `${totalPrice} TL · ${people} kişi` : `${totalPrice} TL`}
              </span>
            )}
            {people > 1 && route.fee != null && (
              <span className="text-xs text-muted tabular-nums">kişi başı {route.fee} TL</span>
            )}
            {badges.map((badge) => (
              <span key={badge} className="rounded-full bg-accent px-2 py-0.5 text-xs font-bold text-accent-ink">
                {badge}
              </span>
            ))}
          </div>
          <p className="mt-1 break-words text-xs text-muted">
            {route.departure_time} – {route.arrival_time}
            {route.walking_distance_m > 0 && ` · ${Math.round(route.walking_distance_m)} m yürüyüş`}
            {' · '}
            {route.legs
              .filter((leg) => leg.type !== 'walking')
              .map((leg) => leg.name ?? leg.line)
              .filter((name, index, all) => name && all.indexOf(name) === index)
              .join(', ')}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {routeVehicleIcons(route).map((Icon, index) => (
            <Icon key={index} className="h-4 w-4 text-muted" />
          ))}
          <IconChevronRight
            className={`h-4 w-4 shrink-0 text-muted transition-transform ${selected ? 'rotate-90' : ''}`}
          />
        </div>
      </button>

      {selected && (
        <div className="border-t border-line px-4 py-1.5">
          <ol className="divide-y divide-line/60">
            {route.legs.map((leg, index) => (
              <LegRow
                key={index}
                leg={leg}
                showDeparture={departureLegs?.has(departureLegKey(leg))}
                lat={lat}
                lon={lon}
                step={index + 1}
              />
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

const RAIL_TYPES = new Set([
  'metro',
  'marmaray',
  'funicular',
  'funikular',
  'tram',
  'teleferik',
  'rail',
  'nostalgic',
])

export function isRailRoute(route: TransitRoute): boolean {
  return route.legs.some(
    (leg) => leg.type !== 'walking' && RAIL_TYPES.has(leg.type.toLowerCase()),
  )
}

const METRO_TYPE_PATTERN = /METRO|MARMARAY|FUNICULAR|FUNIKULAR|SUBWAY|RAIL/

export function isMetroRoute(route: TransitRoute): boolean {
  return route.legs.some(
    (leg) => leg.type !== 'walking' && METRO_TYPE_PATTERN.test(leg.type.toUpperCase()),
  )
}

export function isTramRoute(route: TransitRoute): boolean {
  return route.legs.some((leg) => {
    if (leg.type === 'walking') return false

    const type = leg.type.toUpperCase()

    return type === 'TRAM' || type === 'TRAMVAY' || /NOSTAL|TRAMWAY/.test(type)
  })
}

// Rotada kullanilan arac tiplerinin ikon listesi (tekrarsiz, sirali)
const VEHICLE_ICON_ORDER: { test: (type: string) => boolean; icon: typeof IconBus }[] = [
  { test: (t) => /FERRY|VAPUR|TURYOL|SHAT|SEHIR_HATLARI/.test(t), icon: IconFerry },
  { test: (t) => /METRO|MARMARAY|TRAM|FUNIC|CABLE|NOSTAL|RAIL/.test(t), icon: IconMetro },
  { test: (t) => /TAKSI|DOLMUS|MINIBUS/.test(t), icon: IconCar },
]

function routeVehicleIcons(route: TransitRoute) {
  const types = route.legs
    .filter((leg) => leg.type !== 'walking')
    .map((leg) => leg.type.toUpperCase())

  const icons: ((props: { className?: string }) => ReactElement)[] = []
  const seen = new Set<string>()

  for (const { test, icon } of VEHICLE_ICON_ORDER) {
    for (const type of types) {
      if (!seen.has(icon.name) && test(type)) {
        seen.add(icon.name)
        icons.push(icon)
        break
      }
    }
  }

  if (icons.length === 0 && types.length > 0) icons.push(IconBus)

  return icons
}

const FERRY_TYPE_PATTERN = /FERRY|VAPUR|TURYOL|SHAT|SEHIR_HATLARI/

export function isFerryRoute(route: TransitRoute): boolean {
  return route.legs.some(
    (leg) => leg.type !== 'walking' && FERRY_TYPE_PATTERN.test(leg.type.toUpperCase()),
  )
}

export function TransitList({
  result,
  mode,
  people,
  selectedIndex,
  onSelect,
}: {
  result: PlanResult
  mode: Mode
  people: number
  selectedIndex: number
  onSelect: (index: number) => void
}) {
  const { routes, recommendations, status, error, source, note } = result.public_transport

  if (status !== 'success' || routes.length === 0) {
    return (
      <div className="rounded-2xl border border-line bg-bg/50 px-4 py-5 text-center text-sm text-muted">
        {error ?? 'Bu iki nokta arasında toplu taşıma rotası bulunamadı.'}
      </div>
    )
  }

  // Deniz modu: vapur içeren rota yoksa net mesaj ver
  if (mode === 'deniz') {
    const ferryRoutes = routes.filter(isFerryRoute)

    if (ferryRoutes.length === 0) {
      return (
        <div className="rounded-2xl border border-line bg-bg/50 px-4 py-5 text-center text-sm text-muted">
          Bu güzergahta deniz ulaşımı (vapur) bulunamadı. Otobüs moduna göz at.
        </div>
      )
    }

    return (
      <div className="space-y-2.5">
        {ferryRoutes.slice(0, 4).map((route, index) => (
          <TransitRouteCard
            key={index}
            route={route}
            people={people}
            badges={getBadges(route, recommendations)}
            selected={index === selectedIndex}
            onSelect={() => onSelect(index)}
            departureLegs={firstBusLegKeys(ferryRoutes.slice(0, 4))}
            lat={result.start_coord.lat}
            lon={result.start_coord.lon}
          />
        ))}

        <p className="pt-1 text-center text-xs text-muted">
          {ferryRoutes.length} deniz rotası · {source ?? 'İETT'} verileriyle
        </p>
      </div>
    )
  }

  // Tramvay modu: tramvay içeren rota yoksa net mesaj ver
  if (mode === 'tramvay') {
    const tramRoutes = routes.filter(isTramRoute)

    if (tramRoutes.length === 0) {
      return (
        <div className="rounded-2xl border border-line bg-bg/50 px-4 py-5 text-center text-sm text-muted">
          Bu güzergahta tramvay hattı bulunamadı. Bu şehirde tramvay verimiz yok
          olabilir; Otobüs moduna göz at.
        </div>
      )
    }

    return (
      <div className="space-y-2.5">
        {tramRoutes.slice(0, 4).map((route, index) => (
          <TransitRouteCard
            key={index}
            route={route}
            people={people}
            badges={getBadges(route, recommendations)}
            selected={index === selectedIndex}
            onSelect={() => onSelect(index)}
            departureLegs={firstBusLegKeys(tramRoutes.slice(0, 4))}
            lat={result.start_coord.lat}
            lon={result.start_coord.lon}
          />
        ))}

        <p className="pt-1 text-center text-xs text-muted">
          {tramRoutes.length} tramvay rotası · {source ?? 'İETT'} verileriyle
        </p>
      </div>
    )
  }

  // Metro modu: raylı sistem içeren rotalar yoksa tüm rotaları göster
  const visibleRoutes =
    mode === 'metro' && routes.some(isRailRoute)
      ? routes.filter(isRailRoute)
      : routes

  return (
    <div className="space-y-2.5">
      {visibleRoutes.slice(0, 4).map((route, index) => (
        <TransitRouteCard
          key={index}
          route={route}
          people={people}
          badges={getBadges(route, recommendations)}
          selected={index === selectedIndex}
          onSelect={() => onSelect(index)}
          departureLegs={firstBusLegKeys(visibleRoutes.slice(0, 4))}
          lat={result.start_coord.lat}
          lon={result.start_coord.lon}
        />
      ))}

      {note && (
        <p className="text-center text-xs text-muted">{note}</p>
      )}

      <p className="pt-1 text-center text-xs text-muted">
        {visibleRoutes.length} rota bulundu · {source ?? 'İETT'} verileriyle · Haritada seçili rota gösterilir
      </p>
    </div>
  )
}

/** Tren modu: rayli rotalar (Marmaray/metro/tramvay) varsa numarali kartlarla goster.
 * Yoksa null doner; cagiran tahmin kartina duser. */
export function RailRouteCards({
  result,
  people,
}: {
  result: PlanResult
  people: number
}) {
  const [index, setIndex] = useState(0)
  const routes = result.public_transport.routes.filter(isRailRoute)

  if (routes.length === 0) return null

  const visible = routes.slice(0, 4)

  return (
    <div className="space-y-2.5">
      <p className="text-xs font-bold uppercase tracking-wide text-accent">
        🚇 Raylı sistem rotaları (gerçek duraklarla)
      </p>
      {visible.map((route, i) => (
        <TransitRouteCard
          key={i}
          route={route}
          people={people}
          badges={getBadges(route, result.public_transport.recommendations)}
          selected={i === index}
          onSelect={() => setIndex(i)}
          departureLegs={firstBusLegKeys(visible)}
          lat={result.start_coord.lat}
          lon={result.start_coord.lon}
        />
      ))}
    </div>
  )
}

/** Ucak/tren tahmini icin somut bilgi paneli (sablon adim YOK).
 * Istasyon ismi ve sefer saati backend'de olmadigi icin yalnizca bilinen
 * gercekler gosterilir: sure, ucret, mesafe + resmi sorgu kanali. */
function EstimateFacts({
  kind,
  from,
  to,
  estimate,
}: {
  kind: 'ucak' | 'tren'
  from: string
  to: string
  estimate: FlightEstimate
}) {
  const hours = Math.floor((estimate.duration_minutes ?? 0) / 60)
  const minutes = (estimate.duration_minutes ?? 0) % 60

  return (
    <div className="mt-3 space-y-2">
      <p className="break-words text-sm font-bold">
        {from} <span className="mx-1 text-accent">→</span> {to}
      </p>
      <dl className="space-y-2 text-sm">
        <div className="flex items-center justify-between gap-2 rounded-xl bg-bg/60 px-3.5 py-2.5">
          <dt className="text-muted">Toplam süre (tahmini)</dt>
          <dd className="font-bold tabular-nums">~{hours} sa {minutes} dk</dd>
        </div>
        <div className="flex items-center justify-between gap-2 rounded-xl bg-bg/60 px-3.5 py-2.5">
          <dt className="text-muted">Kişi başı (tahmini)</dt>
          <dd className="font-bold tabular-nums">
            {estimate.estimated_price_per_person?.toLocaleString('tr-TR')} TL
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2 rounded-xl bg-bg/60 px-3.5 py-2.5">
          <dt className="text-muted">Toplam ({estimate.people} kişi, tahmini)</dt>
          <dd className="font-bold tabular-nums text-accent">
            {estimate.total_price?.toLocaleString('tr-TR')} TL
          </dd>
        </div>
      </dl>
      <p className="text-[11px] text-muted">
        Net istasyon, saat ve koltuk bilgisi için {kind === 'ucak' ? 'havayolu' : 'TCDD'} sorgulaması gerekir.
      </p>
    </div>
  )
}

export function FlightDetails({ flight, from, to }: { flight: FlightEstimate; from: string; to: string }) {
  if (!flight.available) {
    return (
      <div>
        <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {flight.reason ?? 'Bu mesafe için uçak önerilmiyor.'}
        </p>
        <p className="mt-2 text-center text-xs text-muted">
          Alternatif olarak Araç veya Otobüs moduna bakabilirsin.
        </p>
      </div>
    )
  }

  const [showDetail, setShowDetail] = useState(false)
  const hours = Math.floor((flight.duration_minutes ?? 0) / 60)
  const minutes = (flight.duration_minutes ?? 0) % 60
  return (
    <div>
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <IconPlane className="h-4.5 w-4.5" />
        </span>
        <div className="flex-1">
          <p className="text-sm font-bold">Uçakla (tahmini)</p>
          <p className="text-xs text-muted">
            Toplam ~{hours} sa {minutes} dk (tahmini) · havalimanı süreçleri dahil
          </p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <div className="rounded-xl bg-bg/60 px-3.5 py-3">
          <p className="text-xs text-muted">Kişi başı (tahmini)</p>
          <p className="text-lg font-bold tabular-nums">
            {flight.estimated_price_per_person?.toLocaleString('tr-TR')} TL
          </p>
        </div>
        <div className="rounded-xl bg-bg/60 px-3.5 py-3">
          <p className="text-xs text-muted">
            Toplam ({flight.people} kişi)
          </p>
          <p className="text-lg font-bold tabular-nums text-accent">
            {flight.total_price?.toLocaleString('tr-TR')} TL
          </p>
        </div>
      </div>

      <p className="mt-3 text-xs text-muted">{flight.note}</p>

      <button
        type="button"
        onClick={() => setShowDetail((open) => !open)}
        aria-expanded={showDetail}
        className="mt-2 inline-block text-xs font-bold text-accent underline-offset-2 hover:underline"
      >
        {showDetail ? 'Detayı gizle ↑' : 'Detayı gör →'}
      </button>

      {showDetail && (
        <EstimateFacts kind="ucak" from={from} to={to} estimate={flight} />
      )}
    </div>
  )
}

export function TrainDetails({ train, from, to }: { train: TrainEstimate; from: string; to: string }) {
  if (!train.available) {
    return (
      <div>
        <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
          {train.reason ?? 'Bu mesafe için tren önerilmiyor.'}
        </p>
        <p className="mt-2 text-center text-xs text-muted">
          Alternatif olarak Otobüs veya Araç moduna bakabilirsin.
        </p>
      </div>
    )
  }

  const [showTrainDetail, setShowTrainDetail] = useState(false)
  const hours = Math.floor((train.duration_minutes ?? 0) / 60)
  const minutes = (train.duration_minutes ?? 0) % 60

  return (
    <div>
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <IconTrain className="h-4.5 w-4.5" />
        </span>
        <div className="flex-1">
          <p className="text-sm font-bold">Trenle (tahmini)</p>
          <p className="text-xs text-muted">
            Toplam ~{hours} sa {minutes} dk (tahmini) · istasyon süreçleri dahil
          </p>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <div className="rounded-xl bg-bg/60 px-3.5 py-3">
          <p className="text-xs text-muted">Kişi başı (tahmini)</p>
          <p className="text-lg font-bold tabular-nums">
            {train.estimated_price_per_person?.toLocaleString('tr-TR')} TL
          </p>
        </div>
        <div className="rounded-xl bg-bg/60 px-3.5 py-3">
          <p className="text-xs text-muted">
            Toplam ({train.people} kişi)
          </p>
          <p className="text-lg font-bold tabular-nums text-accent">
            {train.total_price?.toLocaleString('tr-TR')} TL
          </p>
        </div>
      </div>

      <p className="mt-3 text-xs text-muted">{train.note}</p>

      <button
        type="button"
        onClick={() => setShowTrainDetail((open) => !open)}
        aria-expanded={showTrainDetail}
        className="mt-2 inline-block text-xs font-bold text-accent underline-offset-2 hover:underline"
      >
        {showTrainDetail ? 'Detayı gizle ↑' : 'Detayı gör →'}
      </button>

      {showTrainDetail && (
        <EstimateFacts kind="tren" from={from} to={to} estimate={train} />
      )}

      <button
        type="button"
        onClick={() => void openInApp(TCDD_URL)}
        className="mt-2 block text-xs font-bold text-accent underline-offset-2 hover:underline"
      >
        TCDD Seferlerini Gör →
      </button>
    </div>
  )
}

export default function RouteResults({
  mode,
  result,
  people = 1,
  selectedIndex,
  onSelectIndex,
}: {
  mode: Mode
  result: PlanResult
  people?: number
  selectedIndex: number
  onSelectIndex: (index: number) => void
}) {
  const recommendations = result.recommendations ?? result.public_transport.recommendations

  // Sehir adini baslangic noktasindan turet (bilinen sehir listesiyle eslestir)
  const city = extractCity(result.start)

  return (
    <div className="mt-4 space-y-3 rounded-2xl border border-line bg-surface-2/90 p-4" role="region" aria-label="Rota sonuçları">
      <DepartureCityContext.Provider value={city}>
      {(mode === 'arac' || mode === 'motosiklet') &&
        (result.car ? (
          <CarDetails car={result.car} people={people} />
        ) : (
          <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {result.car_error ?? 'Araç bilgisi hesaplanamadı.'}
          </p>
        ))}
      {mode === 'yuruyus' && <WalkingDetails result={result} />}
      {mode === 'ucak' && (
        result.flight ? (
          <FlightDetails flight={result.flight} from={result.start} to={result.destination} />
        ) : (
          <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            Uçak bilgisi hesaplanamadı.
          </p>
        )
      )}
      {mode === 'tren' && (
        result.train ? (
          <>
            <RailRouteCards result={result} people={people} />
            <div className="mt-3">
              <TrainDetails train={result.train} from={result.start} to={result.destination} />
            </div>
          </>
        ) : (
          <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            Tren bilgisi hesaplanamadı.
          </p>
        )
      )}
      {(mode === 'otobus' || mode === 'metro' || mode === 'deniz' || mode === 'tramvay' || mode === 'tumu') && (
        <TransitList
          result={{ ...result, recommendations }}
          mode={mode}
          people={people}
          selectedIndex={selectedIndex}
          onSelect={onSelectIndex}
        />
      )}

      <div className="flex items-center gap-2 border-t border-line pt-3 text-xs text-muted">
        <IconRoute className="h-4 w-4 shrink-0" />
        <span className="min-w-0 flex-1 break-words">{result.start}</span>
        <span aria-hidden="true" className="shrink-0">→</span>
        <span className="min-w-0 flex-1 break-words text-right">{result.destination}</span>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted">
        <span className="flex items-center gap-1">
          <IconClock className="h-3.5 w-3.5" /> Anlık hesaplandı
        </span>
        <span className="ml-auto flex items-center gap-1">
          <IconWallet className="h-3.5 w-3.5" />
          {mode === 'yuruyus' ? 'Yakıt maliyeti dahil değil' : mode === 'motosiklet' ? 'Yakıt maliyeti (motosiklet) dahil' : mode === 'arac' ? 'Yakıt maliyeti dahil' : 'Ücretler yaklaşık'}
        </span>
      </div>
      </DepartureCityContext.Provider>
    </div>
  )
}
