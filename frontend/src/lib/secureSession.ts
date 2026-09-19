import { Capacitor, registerPlugin } from '@capacitor/core'

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

export async function loadSecureValue(key: string): Promise<string | null> {
  if (!usesEncryptedNativeStorage()) {
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  }
  const result = await EncryptedStorage.get({ key })
  return result.value
}

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

  if (value === null) await EncryptedStorage.remove({ key })
  else await EncryptedStorage.set({ key, value })
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
