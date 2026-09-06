import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { LatLng, PlanResult } from '@/lib/api'
import { isFerryRoute, isRailRoute, isTramRoute } from '@/components/RouteResults'

const ACCENT = '#2dd4bf'

const TILE_URL =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'
const TILE_ATTRIBUTION =
  'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ &mdash; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

export type MapMode = 'tumu' | 'otobus' | 'metro' | 'tramvay' | 'yuruyus' | 'arac' | 'motosiklet' | 'ucak' | 'tren' | 'deniz'

type Path = {
  positions: LatLng[]
  dashed: boolean
}

function startIcon() {
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:16px;height:16px;border-radius:9999px;background:${ACCENT};border:3px solid #e6edf7;box-shadow:0 0 0 2px rgba(45,212,191,.35)"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

function endIcon() {
  return L.divIcon({
    className: '',
    html: `<svg width="30" height="38" viewBox="0 0 30 38" style="display:block;filter:drop-shadow(0 3px 6px rgba(0,0,0,.5))"><path d="M15 1C7.3 1 1 7.3 1 15c0 10.4 14 22 14 22s14-11.6 14-22C29 7.3 22.7 1 15 1Z" fill="${ACCENT}"/><circle cx="15" cy="15" r="6" fill="#0b1220"/></svg>`,
    iconSize: [30, 38],
    iconAnchor: [15, 36],
  })
}

function buildPaths(plan: PlanResult, mode: MapMode, routeIndex: number): Path[] {
  const straight: Path = {
    positions: [
      [plan.start_coord.lat, plan.start_coord.lon],
      [plan.end_coord.lat, plan.end_coord.lon],
    ],
    dashed: true,
  }

  if (mode === 'arac' || mode === 'motosiklet') {
    return plan.car?.geometry?.length
      ? [{ positions: plan.car.geometry, dashed: false }]
      : [straight]
  }

  if (mode === 'yuruyus' || mode === 'ucak' || mode === 'tren') {
    return [straight]
  }

  const allRoutes = plan.public_transport.routes

  // Liste (TransitList) ile harita ayni filtre uygular; boylece
  // listede secilen rota indeksi haritada da ayni rotayi cizer.
  let routes = allRoutes

  if (mode === 'deniz') {
    const ferry = allRoutes.filter(isFerryRoute)
    if (ferry.length) routes = ferry
  }

  if (mode === 'tramvay') {
    const tram = allRoutes.filter(isTramRoute)
    if (tram.length) routes = tram
  }

  if (mode === 'metro') {
    const rail = allRoutes.filter(isRailRoute)
    if (rail.length) routes = rail
  }

  const route = routes[routeIndex] ?? routes[0]

  if (!route) {
    return [straight]
  }

  const paths: Path[] = []
  const legCoords = route.legs
    .map((leg) => leg.coords ?? [])
    .filter((coords) => coords.length > 1)

  if (legCoords.length > 0) {
    for (const coords of legCoords) {
      paths.push({ positions: coords, dashed: false })
    }

    return paths
  }

  return [straight]
}

export default function MapView({
  plan,
  mode,
  routeIndex,
}: {
  plan: PlanResult
  mode: MapMode
  routeIndex: number
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const routeLayerRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    const container = containerRef.current

    if (!container || mapRef.current) return

    const map = L.map(container, {
      zoomControl: false,
      scrollWheelZoom: false,
      doubleClickZoom: true,
      attributionControl: true,
    })

    L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION }).addTo(map)
    routeLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      routeLayerRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const routeLayer = routeLayerRef.current

    if (!map || !routeLayer) return

    routeLayer.clearLayers()

    const start: LatLng = [plan.start_coord.lat, plan.start_coord.lon]
    const end: LatLng = [plan.end_coord.lat, plan.end_coord.lon]
    const paths = buildPaths(plan, mode, routeIndex)

    for (const path of paths) {
      L.polyline(path.positions, {
        color: ACCENT,
        weight: 10,
        opacity: 0.18,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(routeLayer)

      L.polyline(path.positions, {
        color: ACCENT,
        weight: 4,
        opacity: 0.95,
        dashArray: path.dashed ? '8 10' : undefined,
        lineCap: 'round',
        lineJoin: 'round',
      }).addTo(routeLayer)
    }

    L.marker(start, { icon: startIcon() }).addTo(routeLayer)
    L.marker(end, { icon: endIcon() }).addTo(routeLayer)

    map.fitBounds(L.latLngBounds(paths.flatMap((path) => path.positions).concat([start, end])), {
      padding: [70, 70],
    })
  }, [plan, mode, routeIndex])

  return <div ref={containerRef} className="absolute inset-0 z-[1] h-full w-full" />
}
