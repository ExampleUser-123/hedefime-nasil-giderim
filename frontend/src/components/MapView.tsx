import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { LatLng, PlanResult } from '@/lib/api'
import { isFerryRoute, isRailRoute, isTramRoute } from '@/components/RouteResults'

const ACCENT = '#2dd4bf'

// %100 ucretsiz, anahtarsiz OpenStreetMap standart katmani (sokak etiketli)
const TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

export type MapMode = 'tumu' | 'otobus' | 'metro' | 'tramvay' | 'yuruyus' | 'arac' | 'motosiklet' | 'ucak' | 'tren' | 'deniz'

type Path = {
  positions: LatLng[]
  dashed: boolean
  /** Su ustu (vapur) cizgisi: 2 nokta bile olsa cizilir, cunku dogru davranis budur. */
  isWater: boolean
}

// KURAL: Karayolu adimlarinda 2 ve daha az noktali cizgi RENDER EDILMEZ.
// Geometri yoksa harita bos kalir; duz cizgi fallback YASAKTIR.

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

export type NearbyStop = {
  name: string
  lat: number
  lon: number
  lines: string[]
}

function stopIcon(lineCount: number) {
  const badge = lineCount > 0 ? String(lineCount) : ''
  return L.divIcon({
    className: '',
    html: `<span style="position:relative;display:block;width:18px;height:18px">
      <span style="position:absolute;inset:0;display:block;width:12px;height:12px;margin:3px;border-radius:9999px;background:#f59e0b;border:2px solid #0b1220;box-shadow:0 0 0 2px rgba(245,158,11,.35)"></span>
      ${badge ? `<span style="position:absolute;top:-6px;right:-6px;min-width:14px;height:14px;padding:0 3px;border-radius:9999px;background:#0b1220;color:#f59e0b;font:700 9px/14px system-ui,sans-serif;text-align:center;border:1px solid #f59e0b">${badge}</span>` : ''}
    </span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  })
}

function transferIcon() {
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:12px;height:12px;border-radius:9999px;background:#e6edf7;border:3px solid ${ACCENT};box-shadow:0 0 0 2px rgba(45,212,191,.3)"></span>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  })
}

type TransferPin = {
  position: LatLng
  title: string
}



/** Ard arda tekrar eden noktalari temizler (cizgi corbasi ve gereksiz dugum onlenir). */
function cleanPositions(positions: LatLng[]): LatLng[] {
  const out: LatLng[] = []
  for (const p of positions) {
    const last = out[out.length - 1]
    if (!last || last[0] !== p[0] || last[1] !== p[1]) out.push(p)
  }
  return out
}

/**
 * TEK adim segmentini izole cizer (glow + solid). Tum rota asla tek dizide
 * birlestirilmez; her leg kendi katmaniyla cizilir.
 */
function drawLegSegment(
  routeLayer: L.LayerGroup,
  positions: LatLng[],
  opts: { dashed?: boolean } = {},
): { glow: L.Polyline; solid: L.Polyline } | null {
  const clean = cleanPositions(positions)
  if (clean.length < 2) return null
  const glow = L.polyline(clean, {
    color: ACCENT,
    weight: 10,
    opacity: 0.18,
    lineCap: 'round',
    lineJoin: 'round',
  }).addTo(routeLayer)
  const solid = L.polyline(clean, {
    color: ACCENT,
    weight: 4,
    opacity: 0.95,
    dashArray: opts.dashed ? '8 10' : undefined,
    lineCap: 'round',
    lineJoin: 'round',
  }).addTo(routeLayer)
  return { glow, solid }
}

/** Secili rotanin binis/inis duraklari (aktarma noktalari dahil). */
function buildTransferPins(
  plan: PlanResult,
  mode: MapMode,
  routeIndex: number,
): TransferPin[] {
  if (mode === 'arac' || mode === 'motosiklet' || mode === 'yuruyus' || mode === 'ucak') {
    return []
  }

  let routes = plan.public_transport.routes

  if (mode === 'deniz') {
    const ferry = routes.filter(isFerryRoute)
    if (ferry.length) routes = ferry
  }

  if (mode === 'tramvay') {
    const tram = routes.filter(isTramRoute)
    if (tram.length) routes = tram
  }

  if (mode === 'metro') {
    const rail = routes.filter(isRailRoute)
    if (rail.length) routes = rail
  }

  const route = routes[routeIndex] ?? routes[0]
  if (!route) return []

  const pins: TransferPin[] = []
  const seen = new Set<string>()

  for (const leg of route.legs) {
    if (leg.type === 'walking') continue
    const coords = leg.coords ?? []
    if (coords.length < 2) continue
    const line = leg.line ?? leg.name ?? ''
    const stops: [LatLng, string | null][] = [
      [coords[0], leg.from_stop],
      [coords[coords.length - 1], leg.to_stop],
    ]
    for (const [position, stop] of stops) {
      const key = `${position[0].toFixed(5)},${position[1].toFixed(5)}|${line}|${stop ?? ''}`
      if (seen.has(key)) continue
      seen.add(key)
      const title = [line, stop].filter(Boolean).join(' · ') || 'Durak'
      pins.push({ position, title })
    }
  }

  return pins
}

function isWaterLeg(legType: string): boolean {
  return /FERRY|VAPUR|DENIZ/.test((legType || '').toUpperCase())
}

function buildPaths(plan: PlanResult, mode: MapMode, routeIndex: number): Path[] {
  // Ucak: kus ucusu gercektir (hava yolu); kesikli cizgi korunur.
  if (mode === 'ucak') {
    return [{
      positions: [
        [plan.start_coord.lat, plan.start_coord.lon],
        [plan.end_coord.lat, plan.end_coord.lon],
      ],
      dashed: true,
      isWater: false,
    }]
  }

  if (mode === 'arac' || mode === 'motosiklet') {
    const geometry = plan.car?.geometry ?? []
    // Geometri yoksa veya 2 ve daha az noktaysa HICBIR SEY cizilmez.
    if (geometry.length <= 2) return []
    return [{ positions: geometry, dashed: false, isWater: false }]
  }

  if (mode === 'yuruyus') {
    // Saf yuruyus geometrisi planda yok; duz cizgi YASAK oldugu icin bos donulur.
    return []
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

  if (mode === 'metro' || mode === 'tren') {
    const rail = allRoutes.filter(isRailRoute)
    if (rail.length) routes = rail
  }

  const route = routes[routeIndex] ?? routes[0]

  if (!route) {
    return []
  }

  // Her adim kendi izolasyonunda; karayolunda 2 ve daha az nokta CIzILMEZ.
  // Vapur (su ustu) 2 nokta bile olsa cizilir: dogru davranis budur.
  const paths: Path[] = []
  for (const leg of route.legs) {
    const coords = leg.coords ?? []
    if (coords.length <= 2 && !isWaterLeg(leg.type)) continue
    if (coords.length < 2) continue
    paths.push({ positions: coords, dashed: false, isWater: isWaterLeg(leg.type) })
  }

  return paths
}

export default function MapView({
  plan,
  mode,
  routeIndex,
  nearbyStops,
  onSelectStop,
  highlight,
}: {
  plan: PlanResult
  mode: MapMode
  routeIndex: number
  nearbyStops?: NearbyStop[]
  onSelectStop?: (stop: NearbyStop) => void
  /** Hat detayi acilinca vurgulanan geometri (belirgin amber cizgi) */
  highlight?: LatLng[] | null
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<L.Map | null>(null)
  const routeLayerRef = useRef<L.LayerGroup | null>(null)
  const stopsLayerRef = useRef<L.LayerGroup | null>(null)
  const highlightLayerRef = useRef<L.LayerGroup | null>(null)
  const boundsRef = useRef<L.LatLngBounds | null>(null)

  useEffect(() => {
    const container = containerRef.current

    if (!container || mapRef.current) return

    const map = L.map(container, {
      zoomControl: false,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      dragging: true,
      touchZoom: true,
      boxZoom: true,
      keyboard: true,
      attributionControl: true,
    })

    L.tileLayer(TILE_URL, {
      attribution: TILE_ATTRIBUTION,
      subdomains: 'abc',
      maxZoom: 19,
    }).addTo(map)
    routeLayerRef.current = L.layerGroup().addTo(map)
    stopsLayerRef.current = L.layerGroup().addTo(map)
    highlightLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      routeLayerRef.current = null
      stopsLayerRef.current = null
      highlightLayerRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const routeLayer = routeLayerRef.current
    const highlightLayer = highlightLayerRef.current

    if (!map || !routeLayer) return

    // 1) ESKI HER SEYI SIL: rota katmani + onceki secim vurgusu.
    //    Yeni sorguda eski cizgi kalirsa orumcek agi olur.
    routeLayer.clearLayers()
    highlightLayer?.clearLayers()

    const start: LatLng = [plan.start_coord.lat, plan.start_coord.lon]
    const end: LatLng = [plan.end_coord.lat, plan.end_coord.lon]
    const paths = buildPaths(plan, mode, routeIndex)

    // 2) HER ADIMI KENDI IZOLASYONUNDA CIZ (tek dizi birlestirme yok).
    //    buildPaths zaten 2 ve daha az noktali karayolu adimini elemistir;
    //    geometri yoksa cizgi cizilmez (duz fallback YASAK).
    for (const path of paths) {
      drawLegSegment(routeLayer, path.positions, { dashed: path.dashed })
    }

    L.marker(start, { icon: startIcon() }).addTo(routeLayer)
    L.marker(end, { icon: endIcon() }).addTo(routeLayer)

    // Secili rotanin binis/inis/aktarma pinleri (hat + durak adi; tiklanabilir)
    for (const pin of buildTransferPins(plan, mode, routeIndex)) {
      L.marker(pin.position, { icon: transferIcon(), keyboard: false })
        .bindTooltip(pin.title, { direction: 'top', offset: [0, -6] })
        .bindPopup(pin.title)
        .addTo(routeLayer)
    }

    map.fitBounds(L.latLngBounds(paths.flatMap((path) => path.positions).concat([start, end])), {
      padding: [70, 70],
    })
    boundsRef.current = L.latLngBounds(paths.flatMap((path) => path.positions).concat([start, end]))
  }, [plan, mode, routeIndex])

  useEffect(() => {
    const map = mapRef.current
    const stopsLayer = stopsLayerRef.current

    if (!map || !stopsLayer) return

    stopsLayer.clearLayers()

    if (!nearbyStops?.length) return

    for (const stop of nearbyStops) {
      const marker = L.marker([stop.lat, stop.lon], {
        icon: stopIcon(stop.lines.length),
        zIndexOffset: -500,
        keyboard: false,
      })

      marker.bindTooltip(stop.name, { direction: 'top', offset: [0, -8] })
      marker.bindPopup(stop.name)

      if (onSelectStop) {
        marker.on('click', () => onSelectStop(stop))
      }

      marker.addTo(stopsLayer)
    }
  }, [nearbyStops, onSelectStop])

  // Hat detayi / adim secimi: secili geometriyi belirgin cizgiyle vurgula ve odaklan
  useEffect(() => {
    const highlightLayer = highlightLayerRef.current
    const map = mapRef.current

    if (!highlightLayer) return

    highlightLayer.clearLayers()

    if (!highlight || highlight.length < 2) return

    L.polyline(highlight, {
      color: '#f59e0b',
      weight: 14,
      opacity: 0.25,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(highlightLayer)

    L.polyline(highlight, {
      color: '#f59e0b',
      weight: 5,
      opacity: 1,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(highlightLayer)

    if (map) {
      map.fitBounds(L.latLngBounds(highlight), { padding: [80, 80] })
    }
  }, [highlight])

  function zoomBy(delta: number) {
    const map = mapRef.current
    if (!map) return
    if (delta > 0) map.zoomIn()
    else map.zoomOut()
  }

  function recenter() {
    const map = mapRef.current
    const bounds = boundsRef.current
    if (!map || !bounds) return
    map.fitBounds(bounds, { padding: [70, 70] })
  }

  const controlBtn =
    'flex h-11 w-11 items-center justify-center rounded-full border border-line bg-surface/90 text-lg font-bold text-fg shadow-lg shadow-black/40 backdrop-blur-md transition-colors hover:border-accent hover:text-accent active:scale-95'

  return (
    <div className="absolute inset-0 z-[1] h-full w-full">
      <div ref={containerRef} className="absolute inset-0 z-0" />
      {/* Sag taraf dokunulabilir harita kontrolleri */}
      <div
        className="absolute right-3 top-1/3 z-10 flex flex-col gap-2"
        onPointerDownCapture={(e) => e.stopPropagation()}
        onDoubleClickCapture={(e) => e.stopPropagation()}
      >
        <button type="button" aria-label="Yakınlaş" onClick={() => zoomBy(1)} className={controlBtn}>
          +
        </button>
        <button type="button" aria-label="Uzaklaş" onClick={() => zoomBy(-1)} className={controlBtn}>
          −
        </button>
        <button type="button" aria-label="Rotaya odaklan" onClick={recenter} className={controlBtn}>
          🎯
        </button>
      </div>
    </div>
  )
}
