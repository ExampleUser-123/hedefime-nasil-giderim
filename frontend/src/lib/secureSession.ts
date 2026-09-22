import { Capacitor, registerPlugin } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'

type EncryptedStoragePlugin = {
  get(options: { key: string }): Promise<{ value: string | null }>
  set(options: { key: string; value: string }): Promise<void>
  remove(options: { key: string }): Promise<void>
}

const EncryptedStorage = registerPlugin<EncryptedStoragePlugin>('EncryptedStorage')

export const SESSION_TOKEN_KEY = 'hng-auth-token'
export const SESSION_USER_KEY = 'hng-auth-user'

export function usesEncryptedNativeStorage(): boolean {
  return Capacitor.isNativePlatform()
}

async function readLocal(key: string): Promise<string | null> {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

/**
 * Oturum okuma (oncelikli sira):
 * 1. SQLCipher sifreli depo (en guvenli)
 * 2. Capacitor Preferences (yedek katman — eklenti arizasina dayanikli)
 * 3. WebView localStorage (son care)
 */
export async function loadSecureValue(key: string): Promise<string | null> {
  if (!usesEncryptedNativeStorage()) return readLocal(key)

  try {
    const result = await EncryptedStorage.get({ key })
    if (result.value !== null) return result.value
  } catch {
    // SQLCipher hatasi alt katmanlara dus
  }

  try {
    const { value } = await Preferences.get({ key })
    if (value !== null) return value
  } catch {
    // alt katmana dus
  }

  return readLocal(key)
}

/**
 * Oturum yazma: tum katmanlara best-effort yazar. Biri patlasa bile
 * digerleri oturumu korur; cikis karari kullaniciya aittir.
 */
export async function saveSecureValue(key: string, value: string | null): Promise<void> {
  if (!usesEncryptedNativeStorage()) {
    try {
      if (value === null) localStorage.removeItem(key)
      else localStorage.setItem(key, value)
    } catch {
      // localStorage kapaliysa sessizce gec
    }
    return
  }

  if (value === null) {
    await EncryptedStorage.remove({ key }).catch(() => {})
    await Preferences.remove({ key }).catch(() => {})
    try {
      localStorage.removeItem(key)
    } catch {
      // sessizce gec
    }
    return
  }

  await EncryptedStorage.set({ key, value }).catch(() => {})
  await Preferences.set({ key, value }).catch(() => {})
  try {
    localStorage.setItem(key, value)
  } catch {
    // sessizce gec
  }
}

/** Move an existing native WebView session out of localStorage once. */
export async function migrateLegacyNativeValue(key: string): Promise<string | null> {
  const secureValue = await loadSecureValue(key)
  if (secureValue !== null || !usesEncryptedNativeStorage()) return secureValue

  try {
    const legacy = localStorage.getItem(key)
    if (legacy === null) return null
    await saveSecureValue(key, legacy)
    localStorage.removeItem(key)
    return legacy
  } catch {
    return null
  }
}
