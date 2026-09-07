import { Capacitor } from '@capacitor/core'
import { GoogleSignIn } from '@capawesome/capacitor-google-sign-in'
import { authWithGoogle, setAuthToken, type AuthUser } from './api'

const USER_KEY = 'hng-auth-user'

// Google Cloud Console'da olusturulan WEB client ID.
// Backend'deki GOOGLE_CLIENT_ID env'i ile AYNI olmali.
export const GOOGLE_WEB_CLIENT_ID =
  '141606636741-hncceotjp53lov9fkcklvt0krq50pb79.apps.googleusercontent.com'

let initialized = false

export function isAuthed(): boolean {
  return getStoredUser() !== null
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null

    const parsed = JSON.parse(raw) as AuthUser
    return parsed?.id ? parsed : null
  } catch {
    return null
  }
}

function storeUser(user: AuthUser | null) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
    else localStorage.removeItem(USER_KEY)
  } catch {
    // sessizce devam
  }
}

export async function signInWithGoogle(): Promise<AuthUser> {
  if (!GOOGLE_WEB_CLIENT_ID) {
    throw new Error(
      'Google girişi henüz yapılandırılmadı. Google Cloud Console client ID bekleniyor.',
    )
  }

  if (!initialized) {
    await GoogleSignIn.initialize({ clientId: GOOGLE_WEB_CLIENT_ID })
    initialized = true
  }

  const result = await GoogleSignIn.signIn()

  if (!result.idToken) {
    throw new Error('Google girişi yanıt vermedi. Lütfen tekrar dene.')
  }

  const { token, user } = await authWithGoogle(result.idToken)

  setAuthToken(token)
  storeUser(user)

  return user
}

export async function signOut(): Promise<void> {
  setAuthToken(null)
  storeUser(null)

  if (Capacitor.isNativePlatform() && initialized) {
    try {
      await GoogleSignIn.signOut()
    } catch {
      // oturum zaten kapaliysa sorun degil
    }
  }
}

/**
 * Token'in gecerliligini sunucudan kontrol eder.
 * Suresi dolmus token'larda oturumu temizler.
 */
export async function refreshAuthState(): Promise<void> {
  if (!getStoredUser()) return

  const { fetchAuthMe } = await import('./api')

  try {
    await fetchAuthMe()
  } catch {
    await signOut()
  }
}
