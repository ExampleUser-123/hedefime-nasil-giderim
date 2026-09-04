const API_BASE = 'http://127.0.0.1:8000'

export type Mode = 'otobus' | 'metro' | 'yuruyus' | 'arac'

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

export type PlanResult = {
  start: string
  destination: string
  start_coord: Coord
  end_coord: Coord
  car: CarResult
  public_transport: {
    status: string
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data?.error ?? 'Beklenmeyen bir hata oluştu.')
  }

  if (data?.error) {
    throw new Error(data.error)
  }

  return data as T
}

export function fetchPlan(start: string, end: string, people = 1) {
  return request<PlanResult>(
    `/plan?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&people=${people}`,
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
  )
}
