// Varsayilan: canli Render API'si. Lokal gelistirmede .env ile override edilir.
// NOT: Varsayilan localhost OLMAMALI — .env'siz derlenen web/APK aksi halde
// kendi makinesine istek atip "Sunucuya ulasilamadi" verir.
const API_BASE =
  import.meta.env.VITE_API_BASE ?? 'https://hedefime-nasil-giderim.vercel.app'

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
  /** Arac ici / yurume suresi (dk). Yoksa null — uydurulmaz. */
  duration_min?: number | null
  walking_distance_m?: number | null
  walking_duration_min?: number | null
  departure_time: string | null
  arrival_time: string | null
  from_stop: string | null
  to_stop: string | null
  /** Yon/tabela (ham veride varsa). */
  direction?: string | null
  /** Peron (veri kaynaginda yok; her zaman null). */
  platform?: string | null
  /** Hat ucreti (hat bazli veri yok; her zaman null). */
  fare?: number | null
  stops: string[]
  alternate_lines: string[]
  coords?: LatLng[]
  /** Yurume ayaginin gectigi cadde/sokak adlari (OSRM steps; yoksa bos/eksik) */
  streets?: string[]
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
  vehicle_type?: 'arac' | 'motosiklet'
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
  /** Havalimani transfer bacaklari (gercek geometrili; yoksa tahmin karti) */
  legs?: TransitLeg[]
}

export type TrainEstimate = FlightEstimate

export type PlanResult = {
  start: string
  destination: string
  start_coord: Coord
  end_coord: Coord
  car: CarResult | null
  car_error: string | null
  other_vehicle?: CarResult | null
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

import { SESSION_TOKEN_KEY, saveSecureValue } from './secureSession'

let authToken: string | null = null

export function getAuthToken(): string | null {
  return authToken
}

export function setAuthToken(token: string | null) {
  authToken = token
  void saveSecureValue(SESSION_TOKEN_KEY, token).catch(() => {
    // Oturum acma islemi ag basarisini etkilemesin; sonraki acilista tekrar giris gerekir.
  })
}

export function hydrateAuthToken(token: string | null) {
  authToken = token
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 30000): Promise<T> {
  const isGet = (init?.method ?? 'GET') === 'GET'
  let lastError: unknown
  // Geçici bağlantı kopmalarında GET isteklerinde bir kez daha dene
  for (let attempt = 0; attempt < (isGet ? 2 : 1); attempt++) {
    if (attempt > 0) await new Promise((r) => setTimeout(r, 900))
    try {
      return await requestOnce<T>(path, init, timeoutMs)
    } catch (err) {
      lastError = err
      const msg = err instanceof Error ? err.message : ''
      // Ag hatasiysa tekrar dene; HTTP/timeout hatalarinda tekrarlama
      if (!msg.includes('ulaşılamadı')) throw err
    }
  }
  throw lastError
}

async function requestOnce<T>(path: string, init?: RequestInit, timeoutMs = 30000): Promise<T> {
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
    const err = new Error(data?.error ?? data?.detail ?? 'Sunucu bir hata verdi. Lütfen tekrar dene.')
    // Cagiran tarafin ag hatasi ile kimlik hatasini ayirt edebilmesi icin
    ;(err as Error & { status?: number }).status = response.status
    // 429 = gunluk kota doldu; arayuz "üyeliği yükselt" akisini acar
    if (response.status === 429) {
      ;(err as Error & { quota?: boolean }).quota = true
    }
    throw err
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

export function fetchSuggestions(q: string, coords?: { lat: number; lon: number }, timeoutMs = 6000, city?: string): Promise<PlaceSuggestion[]> {
  const params = new URLSearchParams({ q })

  if (coords) {
    params.set('lat', String(coords.lat))
    params.set('lon', String(coords.lon))
  }

  if (city && city.trim()) {
    params.set('city', city.trim())
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
  // Render free tier uykusundan 50-60 sn'de uyanabilir; auth istekleri
  // soguk baslamayi bekleyecek kadar uzun zaman asimina sahip olmali.
  return request<{ token: string; user: AuthUser }>('/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential: idToken }),
  }, 75000)
}

export type RegisterResponse = {
  needs_verification?: boolean
  token?: string
  user?: AuthUser
  message?: string
  email?: string
}

export function registerWithEmail(email: string, password: string, name: string, inviteCode?: string) {
  return request<RegisterResponse>('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name, invite_code: inviteCode ?? '' }),
  }, 75000)
}

export function verifyEmail(email: string, code: string) {
  return request<{ token: string; user: AuthUser; message: string }>('/auth/verify-email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  }, 75000)
}

export function resendVerificationCode(email: string) {
  return request<{ ok: boolean; message: string }>('/auth/resend-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  }, 75000)
}

export function forgotPassword(email: string) {
  return request<{ ok: boolean; message: string }>('/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  }, 75000)
}

export function resetPassword(email: string, code: string, newPassword: string) {
  return request<{ token: string; user: AuthUser; message: string }>('/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code, new_password: newPassword }),
  }, 75000)
}

export function loginWithEmail(email: string, password: string) {
  return request<{ token: string; user: AuthUser; needs_verification?: boolean; email?: string }>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }, 75000)
}

export function fetchAuthMe() {
  return request<{ user: AuthUser }>('/auth/me', undefined, 75000)
}

export function deleteAccount() {
  return request<{ ok: boolean; message: string }>('/auth/delete-account', {
    method: 'DELETE',
  }, 30000)
}

// --- Uyelik katmani ve gunluk kota -------------------------------------------

export type Tier = 'free' | 'lite' | 'premium'

export type UsageInfo = {
  tier: Tier
  routes_used: number
  routes_limit: number // -1 = sinirsiz
  ai_used: number
  ai_limit: number // -1 = sinirsiz
  magic_used?: number
  magic_limit?: number // -1 = sinirsiz
}

export function fetchUsage(): Promise<UsageInfo> {
  return request<UsageInfo>('/usage', undefined, 30000)
}

// --- Magic Share + Vibe + Gamification ---------------------------------------

export type MagicResult = {
  name: string
  address: string
  city: string
  lat: number
  lon: number
  confidence: 'high' | 'medium'
  needs_review: boolean
  usage?: { used: number; limit: number }
}

export function resolveMagicShare(text: string): Promise<MagicResult> {
  return request<MagicResult>('/magic-share', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  }, 30000)
}

export function fetchMagicUsage(): Promise<{ tier: Tier; used: number; limit: number }> {
  return request('/magic-share/usage', undefined, 15000)
}

export type VibeMood = 'sakin' | 'ekonomik' | 'manzarali' | 'kahve'

export type VibeResponse = {
  mood: VibeMood
  order: string[]
  notes: string[]
  highlights: Record<string, string>
  pois: { name: string; detail: string; lat: number; lon: number }[]
  transit_routes: unknown[]
  car: unknown
}

export function fetchVibeRoutes(args: {
  start_lat: number; start_lon: number; end_lat: number; end_lon: number
  city?: string; people?: number; vehicle?: string; mood: VibeMood
}): Promise<VibeResponse> {
  return request<VibeResponse>('/vibe-routes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  }, 45000)
}

export type GameProfile = {
  xp: number
  level: number
  progress: number
  badges: { id: string; name: string; icon: string; desc: string }[]
  badge_ids: string[]
  cities: string[]
  targets_count: number
  xp_gain?: number
  new_badges?: { id: string; name: string; icon: string; desc: string }[]
}

export function fetchGameProfile(): Promise<GameProfile> {
  return request('/gamification/profile', undefined, 15000)
}

export function fetchGameBadges(): Promise<{
  badges: ({ id: string; name: string; icon: string; desc: string; owned: boolean })[]
}> {
  return request('/gamification/badges', undefined, 15000)
}

export function postGameEvent(type: string, meta: Record<string, unknown> = {}): Promise<GameProfile | null> {
  return request<GameProfile>('/gamification/event', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, meta }),
  }, 15000).catch(() => null)
}

export type GameTarget = {
  id: string
  name: string
  address: string
  city: string
  lat: number | null
  lon: number | null
  created_at: string
}

export function fetchTargets(): Promise<GameTarget[]> {
  return request<{ targets: GameTarget[] }>('/targets', undefined, 15000)
    .then((d) => d.targets ?? [])
    .catch(() => [])
}

export function addTarget(t: {
  name: string; lat?: number | null; lon?: number | null; address?: string; city?: string
}): Promise<{ targets: GameTarget[]; profile: GameProfile } | null> {
  return request<{ targets: GameTarget[]; profile: GameProfile }>('/targets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(t),
  }, 15000).catch(() => null)
}

export function deleteTarget(id: string): Promise<{ targets: GameTarget[] } | null> {
  return request<{ targets: GameTarget[] }>(`/targets/${encodeURIComponent(id)}`, { method: 'DELETE' }, 15000)
    .catch(() => null)
}

// --- Marketplace + Davet + XP Store ------------------------------------------

export type CommunityComment = {
  user_id: string
  user_name: string
  text: string
  created: number
}

export type CommunityRoute = {
  id: string
  user_id: string
  user_name: string
  title: string
  description: string
  from: string
  to: string
  mode: string
  people: number
  place: { name: string; address: string; city: string; lat: number | null; lon: number | null }
  image_urls: string[]
  created: number
  rating_avg?: number
  rating_count?: number
  comments?: CommunityComment[]
  comment_count?: number
}

export function fetchMarketplace(limit = 20, offset = 0, sort: 'new' | 'top' = 'new'): Promise<CommunityRoute[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset), sort })
  return request<{ routes: CommunityRoute[] }>(`/marketplace?${params}`, undefined, 15000)
    .then((d) => d.routes ?? [])
    .catch(() => [])
}

export function rateMarketplace(id: string, stars: number): Promise<{
  route: CommunityRoute; profile: GameProfile | null
} | null> {
  return request<{ route: CommunityRoute; profile: GameProfile | null }>(
    `/marketplace/${encodeURIComponent(id)}/rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stars }),
    }, 15000).catch(() => null)
}

export function commentMarketplace(id: string, text: string): Promise<{
  route: CommunityRoute; profile: GameProfile | null
} | null> {
  return request<{ route: CommunityRoute; profile: GameProfile | null }>(
    `/marketplace/${encodeURIComponent(id)}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }, 15000).catch(() => null)
}

export function publishMarketplace(item: {
  title: string; description?: string; from?: string; to?: string; mode?: string
  people?: number; place?: { name?: string; address?: string; city?: string; lat?: number | null; lon?: number | null }
  image_urls?: string[]
}): Promise<{ route: CommunityRoute; profile: GameProfile } | null> {
  return request<{ route: CommunityRoute; profile: GameProfile }>('/marketplace', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  }, 20000).catch(() => null)
}

export function deleteMarketplace(id: string): Promise<boolean> {
  return request<{ ok: boolean }>(`/marketplace/${encodeURIComponent(id)}`, { method: 'DELETE' }, 15000)
    .then((d) => !!d.ok)
    .catch(() => false)
}

// --- Canli yolculuk paylasimi -------------------------------------------------

export type LiveTrip = { id: string; update_key: string }

export function createLiveTrip(args: {
  from: string; destination: string
  dest_lat?: number | null; dest_lon?: number | null
  lat?: number | null; lon?: number | null; eta_min?: number | null
}): Promise<LiveTrip | null> {
  return request<LiveTrip>('/live-trips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  }, 20000).catch(() => null)
}

export function pingLiveTrip(id: string, args: {
  update_key: string; lat: number; lon: number; eta_min?: number | null
}): Promise<boolean> {
  return request<{ ok: boolean }>(`/live-trips/${encodeURIComponent(id)}/ping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(args),
  }, 15000).then((d) => !!d.ok).catch(() => false)
}

export function fetchInviteCode(): Promise<{ code: string | null }> {
  return request<{ code: string | null }>('/invite/code', undefined, 15000).catch(() => ({ code: null }))
}

export type XpStoreItem = {
  id: string
  name: string
  desc: string
  cost: number
  owned: boolean
}

export function fetchXpStore(): Promise<{ xp: number; items: XpStoreItem[] }> {
  return request<{ xp: number; items: XpStoreItem[] }>('/xp-store/items', undefined, 15000).catch(() => ({ xp: 0, items: [] }))
}

export function redeemXpStore(item: string): Promise<{
  ok: boolean; effect: string; profile: GameProfile; perks: Record<string, unknown>
} | null> {
  return request<{
    ok: boolean; effect: string; profile: GameProfile; perks: Record<string, unknown>
  }>('/xp-store/redeem', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item }),
  }, 20000).catch(() => null)
}

/** Odullu reklam sonrasi +1 kota hakki (gunde en fazla 3). Basarisizsa hata firlatir. */
export async function claimAdReward(kind: 'routes' | 'ai' | 'magic'): Promise<{
  ok: boolean; effect: string; remaining: number
}> {
  return request<{ ok: boolean; effect: string; remaining: number }>('/ads/reward', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind }),
  }, 20000)
}

// --- AI rota detayi (adim adim timeline) ------------------------------------

export type RouteStep = {
  step_type: string
  instruction: string
  departure_stop: string | null
  arrival_stop: string | null
  line_name: string | null
  departure_times: string[] | null
  duration: string | null
  walking_distance_m: number | null
  walking_duration_min: number | null
  direction: string | null
  platform: string | null
  fare: number | null
}

export type RouteDetailResponse = {
  total_duration: string
  total_price: string
  total_walking_m: number
  transfer_count: number
  summary_text: string
  steps: RouteStep[]
}

/** Secili rotanin AI destekli adim adim detayi. Hata firlatir. */
export async function fetchRouteDetails(payload: {
  from: string
  to: string
  city?: string
  start_lat?: number
  start_lon?: number
  people?: number
  total_minutes?: number | null
  fee?: number | null
  legs: TransitLeg[]
}): Promise<RouteDetailResponse> {
  return request<RouteDetailResponse>('/route-details', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 45000)
}

// --- Istasyon rehberi (gercek OSM verisi + kisa AI yorumu) -------------------

export type GuideStation = {
  name: string
  lat: number
  lon: number
  distance_m: number
  lines: string[]
}

export type StationGuideResponse = {
  near_start: GuideStation[]
  near_end: GuideStation[]
  guidance: string | null
  frequency_note: string | null
}

export async function fetchNearestStations(lat: number, lon: number): Promise<GuideStation[]> {
  const res = await request<{ stations: GuideStation[] }>(
    `/nearest-stations?lat=${lat}&lon=${lon}`, undefined, 15000,
  ).catch(() => ({ stations: [] }))
  return res.stations ?? []
}

export async function fetchStationGuide(payload: {
  from: string
  to: string
  start_lat: number
  start_lon: number
  end_lat: number
  end_lon: number
}): Promise<StationGuideResponse> {
  return request<StationGuideResponse>('/station-guide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 45000)
}

// --- Kullanici veri-duzeltme bildirimi --------------------------------------

export function reportFeedback(payload: { message: string; context?: string }) {
  return request<{ ok: boolean }>('/reports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }, 15000)
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
  computed_at?: string
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
  computed_at?: string
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
    }, 25000)
    return data?.departures ?? []
  } catch {
    return null
  }
}

// --- Hat detay sayfasi --------------------------------------------------------

export type LineStop = {
  name: string
  lat: number
  lon: number
  distance_m?: number | null
}

export type LineDetails = {
  city: string
  line: string
  name: string | null
  type: string | null
  stop_count: number
  stops: LineStop[]
  next_departures: StopDeparture[]
}

export async function fetchLineDetails(
  city: string,
  line: string,
  lat?: number,
  lon?: number,
): Promise<LineDetails | null> {
  const params = new URLSearchParams({ city, line })
  if (lat != null && lon != null) {
    params.set('lat', String(lat))
    params.set('lon', String(lon))
  }
  try {
    return await request<LineDetails>(`/line-details?${params}`, undefined, 20000)
  } catch {
    return null
  }
}

// --- Cevrimdisi sehir verisi -------------------------------------------------

export type TransitStopRaw = {
  id: string
  name: string
  lat: number
  lon: number
  lines?: { n: string; t?: string; l?: string }[]
}

export function fetchTransitDataCity(
  city: string,
): Promise<{ city: string; stops: TransitStopRaw[]; count: number }> {
  return request(`/transit-data/${encodeURIComponent(city)}`, undefined, 120000)
}

export function fetchOfflineCityList(): Promise<string[]> {
  return request<{ cities: string[] }>('/transit-data', undefined, 15000)
    .then((d) => d.cities ?? [])
    .catch(() => [])
}

// --- Paylasim linkleri -------------------------------------------------------

export type ShareRouteParams = {
  start: string
  destination: string
  people: number
  mode: string
}

export function createShareRoute(params: ShareRouteParams): Promise<{ id: string; url: string }> {
  return request('/share-route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  }, 15000)
}

export function fetchShareRoute(id: string): Promise<ShareRouteParams> {
  return request(`/share-route/${encodeURIComponent(id)}`, undefined, 15000)
}

// --- Doluluk bildirimleri ----------------------------------------------------

export type CrowdingLevel = 'empty' | 'normal' | 'crowded' | 'packed'

export function postCrowding(
  city: string,
  line: string,
  level: CrowdingLevel | '',
  punctuality?: 'on_time' | 'late',
): Promise<{ ok: boolean }> {
  return request('/crowding', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city, line, level, punctuality: punctuality ?? '' }),
  }, 10000)
}

export function fetchCrowdingSummary(
  city: string,
  lines: string[],
): Promise<Record<string, { total: number; counts: Record<string, number>; crowded_share: number; punct: Record<string, number> }>> {
  const params = new URLSearchParams({ city, lines: lines.slice(0, 12).join(',') })
  return request(`/crowding?${params}`, undefined, 10000)
}
