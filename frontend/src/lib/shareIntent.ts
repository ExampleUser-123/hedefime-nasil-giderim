import { Capacitor } from '@capacitor/core'
import { CapacitorShareTarget } from '@capgo/capacitor-share-target'

/**
 * Native paylasim karsilama (@capgo/capacitor-share-target).
 * Instagram/WhatsApp vb. "Paylas -> Hedefime Nasil Giderim" ile gelen
 * metinleri kuyruga alir; MagicShare acilisinda tuketilir.
 * Web'de sessizce devre disi.
 */

let pending: string | null = null
let listening = false

export function consumePendingShare(): string | null {
  const value = pending
  pending = null
  return value
}

export function initShareListener(): void {
  if (listening || !Capacitor.isNativePlatform()) return
  listening = true
  try {
    void CapacitorShareTarget.addListener('shareReceived', (event) => {
      const texts = (event.texts ?? []).filter(Boolean)
      const title = (event.title ?? '').trim()
      const combined = [...(title ? [title] : []), ...texts].join('\n').trim()
      if (combined) pending = combined
    }).catch(() => {})
  } catch {
    // eklenti yoksa paylasim karsilama devre disi
  }
}
