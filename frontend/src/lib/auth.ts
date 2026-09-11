import { Capacitor } from '@capacitor/core'
import { GoogleSignIn } from '@capawesome/capacitor-google-sign-in'
import { authWithGoogle, loginWithEmail, registerWithEmail, setAuthToken, type AuthUser } from './api'

const USER_KEY = 'hng-auth-user'

// Google Cloud Console'da olusturulan WEB client ID.
// Backend'deki GOOGLE_CLIENT_ID env'i ile AYNI olmali.
export const GOOGLE_WEB_CLIENT_ID =
  '141606636741-hncceotjp53lov9fkcklvt0krq50pb79.apps.googleusercontent.com'

let initialized = false

// Web'de Google, kullaniciyi bu adrese geri yonderir (bulundugu sayfa).
// Bu adres Google Cloud Console'daki Web client'in "Authorized redirect URIs"
// listesinde de olmalidir.
function webRedirectUrl(): string {
  return window.location.origin + window.location.pathname
}

async function ensureInitialized(): Promise<void> {
  if (initialized) return
  const isWeb = Capacitor.getPlatform() === 'web'
  await GoogleSignIn.initialize({
    clientId: GOOGLE_WEB_CLIENT_ID,
    ...(isWeb ? { redirectUrl: webRedirectUrl() } : {}),
  })
  initialized = true
}

/**
 * Web'de Google'dan geri dondugumuzde URL hash'indeki id_token'i isler.
 * Uygulama acilisinda (main.tsx) bir kez cagrilir; token varsa oturum acilir.
 * Donus degeri: redirect akisiyla giris yapildi mi.
 */
export async function handleGoogleRedirect(): Promise<boolean> {
  if (Capacitor.getPlatform() !== 'web') return false

  const hash = window.location.hash
  if (!hash || (!hash.includes('id_token=') && !hash.includes('error='))) return false

  await ensureInitialized()

  try {
    const webImpl = GoogleSignIn as unknown as {
      handleRedirectCallback: () => Promise<{ idToken?: string }>
    }
    const result = await webImpl.handleRedirectCallback()
    if (!result.idToken) return false

    const { token, user } = await authWithGoogle(result.idToken)
    setAuthToken(token)
    storeUser(user)
    return true
  } catch {
    // Hatali/eksik hash temizlenir; aksi halde her yuklemede tekrar denenir
    window.history.replaceState({}, document.title, window.location.pathname + window.location.search)
    return false
  }
}

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

  await ensureInitialized()

  const result = await GoogleSignIn.signIn()

  if (!result.idToken) {
    throw new Error('Google girişi yanıt vermedi. Lütfen tekrar dene.')
  }

  const { token, user } = await authWithGoogle(result.idToken)

  setAuthToken(token)
  storeUser(user)

  return user
}

export async function signInWithEmail(email: string, password: string): Promise<AuthUser> {
  const { token, user } = await loginWithEmail(email.trim(), password)

  setAuthToken(token)
  storeUser(user)

  return user
}

export async function signUpWithEmail(email: string, password: string, name: string): Promise<AuthUser> {
  const { token, user } = await registerWithEmail(email.trim(), password, name.trim())

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
 * YALNIZCA sunucu net 401 donunce (token suresi bitti/gecersiz) oturumu
 * temizler. Ag hatasi / sunucu uyudu / 5xx durumlarinda oturum korunur —
 * Render uykudan uyanirken kullaniciyi haksiz yere attirmasin.
 */
export async function refreshAuthState(): Promise<void> {
  if (!getStoredUser()) return

  const { fetchAuthMe } = await import('./api')

  try {
    await fetchAuthMe()
  } catch (e) {
    const status = (e as Error & { status?: number }).status

    if (status === 401) {
      await signOut()
    }
    // Diger hatalar (ag, timeout, 502...) sessizce yutulur; oturum kalir
  }
}
