import { reverseGeocode } from './api'
import { getCurrentLocation } from './geolocation'

export type OpenRouteFn = (entry: {
  from: string
  to: string
  people: number
  mode: string
}) => void

/**
 * "Buraya Git": cikis = cihaz GPS konumu (ters-adres etiketiyle),
 * varis = verilen hedef. openRoute preset akisi aramayi otomatik baslatir.
 * Konum alinamazsa hata mesaji doner (rota acilmaz).
 */
export async function goToPlace(
  destination: string,
  onOpenRoute: OpenRouteFn,
): Promise<{ ok: true } | { ok: false; message: string }> {
  const loc = await getCurrentLocation()
  if (!loc.ok) return { ok: false, message: loc.message }

  const { lat, lon } = loc.coords
  let from = `${lat.toFixed(5)},${lon.toFixed(5)}`
  try {
    const place = await reverseGeocode(lat, lon)
    const label = place.display_name.split(',').slice(0, 2).join(',').trim()
    if (label) from = label
  } catch {
    // etiket alinamazsa koordinat metni yeterli (backend cozer)
  }

  onOpenRoute({ from, to: destination, people: 1, mode: 'tumu' })
  return { ok: true }
}
