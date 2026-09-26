/** Neon harita temasi (XP Magazasi map_theme urunu).
 * Secim localStorage'da durur; <html data-theme="neon"> uzerinden
 * Tailwind renk degiskenleri ve harita cizgi rengi degisir. */

const KEY = 'hng-map-theme'

export type MapTheme = 'default' | 'neon'

export const NEON_ACCENT = '#e879f9'
export const DEFAULT_ACCENT = '#2dd4bf'

export function getMapTheme(): MapTheme {
  try {
    return localStorage.getItem(KEY) === 'neon' ? 'neon' : 'default'
  } catch {
    return 'default'
  }
}

export function setMapTheme(theme: MapTheme): void {
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    // depolama kapaliysa yalnizca oturumluk uygula
  }
  if (typeof document !== 'undefined') {
    if (theme === 'neon') document.documentElement.dataset.theme = 'neon'
    else delete document.documentElement.dataset.theme
  }
}

/** Harita cizgileri icin o anki vurgu rengi. */
export function mapAccent(): string {
  if (typeof document !== 'undefined' && document.documentElement.dataset.theme === 'neon') {
    return NEON_ACCENT
  }
  return DEFAULT_ACCENT
}

// Uygulama acilisinda kayitli temayi uygula (tarayici ortaminda)
if (typeof document !== 'undefined') {
  try {
    if (localStorage.getItem(KEY) === 'neon') {
      document.documentElement.dataset.theme = 'neon'
    }
  } catch {
    // sessiz gec
  }
}
