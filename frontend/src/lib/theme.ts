/** Neon harita temasi (XP Magazasi map_theme urunu) + Cyberpunk arayuz
 * temasi (XP Magazasi cyberpunk_theme urunu).
 * Secimler localStorage'da durur; <html data-theme="..."> uzerinden
 * Tailwind renk degiskenleri ve harita cizgi rengi degisir.
 * Cyberpunk aktifken tum paleti ezer (neon harita temasina onceliklidir). */

const KEY = 'hng-map-theme'
const UI_KEY = 'hng-ui-theme'
const UNLOCKED_KEY = 'hng-unlocked-themes'

export type MapTheme = 'default' | 'neon'
export type UiTheme = 'default' | 'cyberpunk'

export const NEON_ACCENT = '#e879f9'
export const DEFAULT_ACCENT = '#2dd4bf'
export const CYBERPUNK_ACCENT = '#ff007f'

export function getMapTheme(): MapTheme {
  try {
    return localStorage.getItem(KEY) === 'neon' ? 'neon' : 'default'
  } catch {
    return 'default'
  }
}

/** Aktif arayuz temasi (varsayilan ya da cyberpunk). */
export function getUiTheme(): UiTheme {
  try {
    return localStorage.getItem(UI_KEY) === 'cyberpunk' ? 'cyberpunk' : 'default'
  } catch {
    return 'default'
  }
}

export function setUiTheme(theme: UiTheme): void {
  try {
    localStorage.setItem(UI_KEY, theme)
  } catch {
    // depolama kapaliysa yalnizca oturumluk uygula
  }
  applyThemes()
}

/** Satin alinmis tema kimlikleri (or. ["cyberpunk"]). Sunucu sahipligi
 * esas kaynaktir; bu liste yalnizca cevrimdisi gosterge icin aynalanir. */
export function getUnlockedThemes(): string[] {
  try {
    const raw = localStorage.getItem(UNLOCKED_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter((t): t is string => typeof t === 'string') : []
  } catch {
    return []
  }
}

export function unlockTheme(id: string): void {
  try {
    const current = getUnlockedThemes()
    if (!current.includes(id)) {
      localStorage.setItem(UNLOCKED_KEY, JSON.stringify([...current, id]))
    }
  } catch {
    // sessiz gec
  }
}

/** Kayitli secimlere gore kok elemana etkin temayi uygular. */
export function applyThemes(): void {
  if (typeof document === 'undefined') return
  const ui = getUiTheme()
  if (ui === 'cyberpunk') {
    document.documentElement.dataset.theme = 'cyberpunk'
    return
  }
  if (getMapTheme() === 'neon') {
    document.documentElement.dataset.theme = 'neon'
    return
  }
  delete document.documentElement.dataset.theme
}

export function setMapTheme(theme: MapTheme): void {
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    // depolama kapaliysa yalnizca oturumluk uygula
  }
  applyThemes()
}

/** Harita cizgileri icin o anki vurgu rengi. */
export function mapAccent(): string {
  if (typeof document !== 'undefined' && document.documentElement.dataset.theme === 'cyberpunk') {
    return CYBERPUNK_ACCENT
  }
  if (typeof document !== 'undefined' && document.documentElement.dataset.theme === 'neon') {
    return NEON_ACCENT
  }
  return DEFAULT_ACCENT
}

// Uygulama acilisinda kayitli temayi uygula (tarayici ortaminda)
if (typeof document !== 'undefined') {
  try {
    applyThemes()
  } catch {
    // sessiz gec
  }
}
