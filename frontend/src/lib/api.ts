const API_BASE =
  import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

export { API_BASE }

export type Mode = 'tumu' | 'otobus' | 'metro' | 'tramvay' | 'yuruyus' | 'arac' | 'motosiklet' | 'ucak' | 'tren' | 'deniz'

export type VehicleType = 'arac' | 'motosiklet'

export type Vehicle = {
  id: string
  name: string
  brand: string
  fuel_type: 'Benzin' | 'Motorin' | 'LPG' | 'Elektrik'
  consumption: number
  vehicle_type: VehicleType
}

export type Place = {
  display_name: string
  lat: number
  lon: number
}

export type LatLng = [number, number]

export type Coord = { lat: number; lon: number }

export type TransitLeg = {
  type: string
  line: string | null
  name: string | null
  route_id: string
  distance_m?: number
  departure_time: string | null
  arrival_time: string | null
  from_stop: string | null
  to_stop: string | null
  stops: string[]
  alternate_lines: string[]
  coords?: LatLng[]
}

export type TransitRoute = {
  fee: number | null
  walking_distance_m: number
  calories_burned: number | null
  co2_emission: number | null
  departure_time: string | null
  arrival_time: string | null
  duration_minutes: number | null
  legs: TransitLeg[]
}

export type CarResult = {
  vehicle: string
  distance_km: number
  duration_minutes: number
  fuel_liters: number
  total_cost: number
  cost_per_person: number
  geometry?: LatLng[]
}

export type FlightEstimate = {
  available: boolean
  reason?: string
  distance_km?: number
  duration_minutes?: number
  estimated_price_per_person?: number
  total_price?: number
  people?: number
  note?: string
}

export type TrainEstimate = FlightEstimate

export type PlanResult = {
  start: string
  destination: string
  start_coord: Coord
  end_coord: Coord
  car: CarResult | null
  car_error: string | null
  vehicle_selected: string
  flight: FlightEstimate | null
  train: TrainEstimate | null
  public_transport: {
    status: string
    error?: string | null
    source?: string
    note?: string
    routes: TransitRoute[]
    recommendations: {
      fastest: TransitRoute | null
      cheapest: TransitRoute | null
      least_walking: TransitRoute | null
    }
  }
  recommendations: PlanResult['public_transport']['recommendations']
}

export type Weather = {
  location: string
  current: {
    temperature: number
    condition: string | null
    wind_speed: number
    humidity: number
  }
  forecast: Array<{
    date: string
    temp_max: number
    temp_min: number
    condition: string | null
    precipitation_probability: number
  }>
}

export type ChatMessage = {
  role: 'user' | 'model'
  text: string
  searchUsed?: boolean
}

const TOKEN_KEY = 'hng-auth-token'

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setAuthToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // localStorage kapaliysa sessizce devam
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 30000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  const headers = new Headers(init?.headers)
  const token = getAuthToken()

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response: Response

  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('İstek çok uzun sürdü. İnternet bağlantını kontrol edip tekrar dene.')
    }

    throw new Error('Sunucuya ulaşılamadı. Backend çalışıyor mu?')
  } finally {
    clearTimeout(timer)
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(data?.error ?? data?.detail ?? 'Sunucu bir hata verdi. Lütfen tekrar dene.')
  }

  if (data?.error) {
    throw new Error(data.error)
  }

  return data as T
}

export type PlaceSuggestion = {
  name: string
  detail: string
  display_name: string
  lat: number
  lon: number
}

export function fetchSuggestions(q: string, coords?: { lat: number; lon: number }, timeoutMs = 6000): Promise<PlaceSuggestion[]> {
  const params = new URLSearchParams({ q })

  if (coords) {
    params.set('lat', String(coords.lat))
    params.set('lon', String(coords.lon))
  }

  return request<{ suggestions: PlaceSuggestion[] }>(
    `/suggest-places?${params}`,
    { method: 'GET' },
    timeoutMs,
  ).then((data) => data.suggestions ?? [])
}

export function fetchPlan(start: string, end: string, people = 1, vehicleId?: string, maxWalk?: number) {
  const params = new URLSearchParams({
    start,
    end,
    people: String(people),
  })

  if (vehicleId) {
    params.set('vehicle', vehicleId)
  }

  if (typeof maxWalk === 'number') {
    params.set('max_walk', String(maxWalk))
  }

  return request<PlanResult>(`/plan?${params.toString()}`, undefined, 45000)
}

export function fetchVehicles() {
  return request<Vehicle[]>('/vehicles', undefined, 15000)
}

export function reverseGeocode(lat: number, lon: number) {
  return request<{ display_name: string; lat: number; lon: number }>(
    `/reverse-geocode?lat=${lat}&lon=${lon}`,
    undefined,
    15000,
  )
}

export function fetchWeather(place: string) {
  return request<Weather>(`/weather?place=${encodeURIComponent(place)}&days=1`)
}

export function createChatSession() {
  return request<{ id: string }>('/chat/sessions', { method: 'POST' })
}

export function sendAssistantMessage(sessionId: string, message: string) {
  return request<{ reply: string; search_used: boolean; session_id: string }>(
    '/ai-assistant',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    },
    90000,
  )
}

export type RouteIntent = {
  start: string | null
  end: string | null
  people: number
  mode: Mode | null
}

export function parseRouteIntent(text: string) {
  return request<RouteIntent>('/parse-intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text }),
  }, 30000)
}

// --- Hesap (auth) + favoriler ----------------------------------------------

export type AuthUser = {
  id: string
  email: string | null
  name: string | null
  picture: string | null
  created_at?: string
}

export type ServerFavorite = {
  id: string
  from: string
  to: string
  people: number
  mode: string
  created_at: string
}

export function authWithGoogle(idToken: string) {
  return request<{ token: string; user: AuthUser }>('/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential: idToken }),
  }, 20000)
}

export function fetchAuthMe() {
  return request<{ user: AuthUser }>('/auth/me', undefined, 15000)
}

export function fetchFavorites() {
  return request<{ favorites: ServerFavorite[] }>('/favorites', undefined, 15000)
}

export function addFavorite(entry: { from: string; to: string; people: number; mode: string }) {
  return request<{ favorites: ServerFavorite[] }>('/favorites', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: entry.from, to: entry.to, people: entry.people, mode: entry.mode }),
  }, 15000)
}

// --- Yaklaşan seferler -------------------------------------------------------

export type NextDeparture = {
  time: string
  source: 'gtfs' | 'tahmini'
  minutes_ahead: number
}

export type NextDeparturesResponse = {
  departures: NextDeparture[]
  city: string
  line: string
  stop: string
}

// 401/404 ve network hatalarinda null doner; UI rozet gostermez, bozulmaz.
export async function fetchNextDepartures(
  city: string,
  line: string,
  stop: string,
  lat?: number,
  lon?: number,
): Promise<NextDeparturesResponse | null> {
  try {
    return await request<NextDeparturesResponse>('/next-departures', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, line, stop, lat, lon }),
    }, 8000)
  } catch {
    return null
  }
}

export function deleteFavorite(id: string) {
  return request<{ favorites: ServerFavorite[] }>(`/favorites/${id}`, {
    method: 'DELETE',
  }, 15000)
}

// --- Yakin duraklar + durak kalkislari ---------------------------------------

export type NearbyStop = {
  city: string
  stop_id: string
  name: string
  lat: number
  lon: number
  distance_m: number
  lines: string[]
}

export type StopDeparture = {
  line: string
  time: string
  source: 'gtfs' | 'tahmini'
  minutes_ahead: number
}

// 401/404 ve network hatalarinda null doner; UI bos liste gosterir, bozulmaz.
export async function fetchNearbyStops(
  lat: number,
  lon: number,
  limit = 8,
): Promise<NearbyStop[] | null> {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    limit: String(limit),
  })

  try {
    const data = await request<{ results: NearbyStop[] }>(`/nearby-stops?${params}`, undefined, 8000)
    return data?.results ?? []
  } catch {
    return null
  }
}

export async function fetchStopDepartures(
  city: string,
  stop: string,
  lat: number,
  lon: number,
  lines: string[],
): Promise<StopDeparture[] | null> {
  try {
    const data = await request<{ departures: StopDeparture[] }>('/stop-departures', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, stop, lat, lon, lines }),
    }, 8000)
    return data?.departures ?? []
  } catch {
    return null
  }
}
