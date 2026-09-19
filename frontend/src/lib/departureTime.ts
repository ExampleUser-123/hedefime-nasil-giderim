/**
 * Kalkis saati yardimcilari (saf fonksiyonlar — React yok, test edilebilir).
 *
 * Kaynak: backend `minutes_ahead` + `computed_at` anlik goruntusu ile
 * CIHAZ saati birlestirilir. Tum duvar-saati gosterimleri Europe/Istanbul
 * ile uretilir; epoch tabanli matematik gece yarisini otomatik cozer.
 */

export const ISTANBUL_TZ = 'Europe/Istanbul'

/** Yetisebilirlik icin guvenlik payi (dk). */
export const CATCH_BUFFER_MIN = 2

export type DepartureLike = {
  time: string
  source: 'gtfs' | 'tahmini'
  minutes_ahead: number
  computed_at?: string
}

/** Backend'in hesabi yaptigi an (epoch ms). Yoksa veri taze sayilir. */
export function computedAtMs(dep: DepartureLike, fallbackNowMs: number): number {
  if (!dep.computed_at) return fallbackNowMs
  const t = Date.parse(dep.computed_at)
  return Number.isFinite(t) ? t : fallbackNowMs
}

/** Hesap anindan bu yana gecen tam dakika (negatif olmaz). */
export function elapsedMin(dep: DepartureLike, nowMs: number): number {
  return Math.max(0, Math.floor((nowMs - computedAtMs(dep, nowMs)) / 60000))
}

/** Cihaz saatine gore guncel kalan sure (dk). Gecmis seferler < 0 doner. */
export function liveMinutesAhead(dep: DepartureLike, nowMs: number): number {
  return dep.minutes_ahead - elapsedMin(dep, nowMs)
}

/** nowMs + deltaMin aninin Istanbul duvar saati (HH:MM, gece yarisi guvenli). */
export function clockAfter(nowMs: number, deltaMin: number): string {
  const fmt = new Intl.DateTimeFormat('tr-TR', {
    timeZone: ISTANBUL_TZ,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  return fmt.format(new Date(nowMs + deltaMin * 60000))
}

/** Kullanicinin yurume suresiyle bu sefere yetisip yetisemeyecegi. */
export function isCatchable(
  dep: DepartureLike,
  walkMin: number,
  bufferMin: number = CATCH_BUFFER_MIN,
  nowMs: number = Date.now(),
): boolean {
  return liveMinutesAhead(dep, nowMs) >= walkMin + bufferMin
}

/** Yetisilebilir ilk sefer (gecmis ve yetisilemezler elenir). */
export function firstCatchable<T extends DepartureLike>(
  departures: T[],
  walkMin: number,
  bufferMin: number = CATCH_BUFFER_MIN,
  nowMs: number = Date.now(),
): T | null {
  let best: T | null = null
  let bestAhead = Number.POSITIVE_INFINITY
  for (const d of departures) {
    const ahead = liveMinutesAhead(d, nowMs)
    if (ahead < walkMin + bufferMin) continue
    if (ahead < bestAhead) {
      bestAhead = ahead
      best = d
    }
  }
  return best
}
