import { useState } from 'react'
import type { CarResult, PlanResult, TransitLeg, TransitRoute } from '@/lib/api'
import {
  IconBus,
  IconCar,
  IconChevronRight,
  IconClock,
  IconMetro,
  IconRoute,
  IconWallet,
  IconWalk,
} from '@/icons'

type Mode = 'otobus' | 'metro' | 'yuruyus' | 'arac'

type Recommendations = PlanResult['recommendations']

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

  return IconBus
}

function CarDetails({ car, people }: { car: CarResult; people: number }) {
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

function WalkingDetails({ car }: { car: CarResult }) {
  const distanceKm = car.distance_km * 1.25
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

function LegRow({ leg }: { leg: TransitLeg }) {
  const Icon = legIcon(leg)

  if (leg.type === 'walking') {
    return (
      <li className="flex items-center gap-3 py-2">
        <Icon className="h-4 w-4 shrink-0 text-muted" />
        <p className="text-sm text-muted">
          {leg.distance_m ? `${Math.round(leg.distance_m)} m yürü` : 'Yürü'}
          <span className="mx-1.5 text-line" aria-hidden="true">·</span>
          {leg.from_stop ?? ''}
          {leg.to_stop && ` → ${leg.to_stop}`}
        </p>
      </li>
    )
  }

  return (
    <li className="flex items-start gap-3 py-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-center gap-1.5 text-sm font-semibold">
          {leg.name ?? leg.line ?? 'Hat'}
          {leg.alternate_lines.length > 0 && (
            <span className="text-xs font-normal text-muted">(+{leg.alternate_lines.length} alternatif)</span>
          )}
        </p>
        <p className="mt-0.5 truncate text-xs text-muted">
          {leg.from_stop} → {leg.to_stop}
          {leg.departure_time && ` · ${leg.departure_time}`}
          {leg.arrival_time && ` – ${leg.arrival_time}`}
          {leg.stops.length > 2 && ` · ${leg.stops.length - 1} durak`}
        </p>
      </div>
    </li>
  )
}

function TransitRouteCard({
  route,
  badges,
  defaultOpen,
}: {
  route: TransitRoute
  badges: string[]
  defaultOpen: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="overflow-hidden rounded-2xl border border-line bg-bg/50">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-surface-2/60"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-base font-bold tabular-nums">{route.duration_minutes ?? '?'} dk</span>
            {route.fee != null && (
              <span className="rounded-full bg-accent/15 px-2 py-0.5 text-xs font-bold text-accent tabular-nums">
                {route.fee} TL
              </span>
            )}
            {badges.map((badge) => (
              <span key={badge} className="rounded-full bg-accent px-2 py-0.5 text-xs font-bold text-accent-ink">
                {badge}
              </span>
            ))}
          </div>
          <p className="mt-1 truncate text-xs text-muted">
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
        <IconChevronRight
          className={`h-4 w-4 shrink-0 text-muted transition-transform ${open ? 'rotate-90' : ''}`}
        />
      </button>

      {open && (
        <div className="border-t border-line px-4 py-1.5">
          <ol className="divide-y divide-line/60">
            {route.legs.map((leg, index) => (
              <LegRow key={index} leg={leg} />
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}

function TransitList({ result }: { result: PlanResult }) {
  const { routes, recommendations, status } = result.public_transport

  if (status !== 'success' || routes.length === 0) {
    return (
      <div className="rounded-2xl border border-line bg-bg/50 px-4 py-5 text-center text-sm text-muted">
        Bu iki nokta arasında toplu taşıma rotası bulunamadı.
      </div>
    )
  }

  return (
    <div className="space-y-2.5">
      {routes.slice(0, 4).map((route, index) => (
        <TransitRouteCard
          key={index}
          route={route}
          badges={getBadges(route, recommendations)}
          defaultOpen={index === 0}
        />
      ))}

      <p className="pt-1 text-center text-xs text-muted">
        {routes.length} rota bulundu · İETT verileriyle
      </p>
    </div>
  )
}

export default function RouteResults({
  mode,
  result,
}: {
  mode: Mode
  result: PlanResult
}) {
  const recommendations = result.recommendations ?? result.public_transport.recommendations

  return (
    <div className="mt-4 space-y-3 rounded-2xl border border-line bg-surface-2/90 p-4" role="region" aria-label="Rota sonuçları">
      {mode === 'arac' && <CarDetails car={result.car} people={1} />}
      {mode === 'yuruyus' && <WalkingDetails car={result.car} />}
      {(mode === 'otobus' || mode === 'metro') && <TransitList result={{ ...result, recommendations }} />}

      <div className="flex items-center gap-2 border-t border-line pt-3 text-xs text-muted">
        <IconRoute className="h-4 w-4 shrink-0" />
        <span className="truncate">{result.start}</span>
        <span aria-hidden="true">→</span>
        <span className="truncate">{result.destination}</span>
      </div>

      <div className="flex items-center gap-3 text-xs text-muted">
        <span className="flex items-center gap-1">
          <IconClock className="h-3.5 w-3.5" /> Anlık hesaplandı
        </span>
        <span className="ml-auto flex items-center gap-1">
          <IconWallet className="h-3.5 w-3.5" />
          {mode === 'arac' ? 'Yakıt maliyeti dahil' : 'Ücretler yaklaşık'}
        </span>
      </div>
    </div>
  )
}
