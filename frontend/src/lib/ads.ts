import { Capacitor } from '@capacitor/core'
import {
  AdMob,
  BannerAdPosition,
  BannerAdSize,
  MaxAdContentRating,
  type BannerAdOptions,
} from '@capacitor-community/admob'

// Gercek AdMob hesabi ID'leri (hesap sahibi: omerfaruk poyraz)
// Uygulama: com.hedefime.giderim
const AD_IDS = {
  banner: 'ca-app-pub-4008793570253978/7070612243',
  rewarded: 'ca-app-pub-4008793570253978/4684122058',
  // Araya giren reklam (interstitial) birimi
  interstitial: 'ca-app-pub-4008793570253978/1400764422',
  // Uygulama acilis reklami (App Open)
  appOpen: 'ca-app-pub-4008793570253978/8876180752',
  // Odullu gecis reklami (Rewarded Interstitial) — kota karsiligi
  rewardInterstitial: 'ca-app-pub-4008793570253978/6586816927',
}

/**
 * Native (Yerel Gelismis) reklam birimi ID'si AdMob panelinde tanimli:
 * ca-app-pub-4008793570253978/4343796963
 * NOT: @capacitor-community/admob eklentisinde Native Ad API'si YOK
 * (banner/reward/interstitial/app-open desteklenir). Bu yuzden sahte
 * "reklam" kutusu cizilmiyor; native icin ayri eklenti gerekir.
 */
export const NATIVE_AD_ID = 'ca-app-pub-4008793570253978/4343796963'
export function isNativeAdSupported(): boolean {
  return false
}

let initialized = false

export function adsAvailable(): boolean {
  return Capacitor.isNativePlatform()
}

export async function initAds(): Promise<void> {
  if (!adsAvailable() || initialized) return

  try {
    await AdMob.initialize({
      initializeForTesting: false,
      maxAdContentRating: MaxAdContentRating.General,
      tagForChildDirectedTreatment: false,
    })
    initialized = true
  } catch (e) {
    console.warn('AdMob baslatilamadi', e)
  }
}

export async function showBottomBanner(): Promise<void> {
  if (!adsAvailable()) return

  try {
    await initAds()
    const options: BannerAdOptions = {
      adId: AD_IDS.banner,
      adSize: BannerAdSize.ADAPTIVE_BANNER,
      position: BannerAdPosition.BOTTOM_CENTER,
    }
    await AdMob.showBanner(options)
  } catch (e) {
    console.warn('Banner gosterilemedi', e)
  }
}

export async function hideBanner(): Promise<void> {
  if (!adsAvailable()) return

  try {
    await AdMob.hideBanner()
  } catch {
    // banner yoksa sessiz gec
  }
}

export async function removeBanner(): Promise<void> {
  if (!adsAvailable()) return

  try {
    await AdMob.removeBanner()
  } catch {
    // banner yoksa sessiz gec
  }
}

/**
 * Odullu reklam gosterir. Kullanici reklami sonuna kadar izlerse true doner.
 * Web/tarayici ortaminda reklam yok; akisi bozmamak icin true doner.
 */
export async function showRewardedAd(): Promise<boolean> {
  if (!adsAvailable()) return true

  try {
    await initAds()
    await AdMob.prepareRewardVideoAd({ adId: AD_IDS.rewarded })
    await AdMob.showRewardVideoAd()
    return true
  } catch (e) {
    console.warn('Odullu reklam gosterilemedi', e)
    return false
  }
}

/**
 * Odullu GECIS reklami (Rewarded Interstitial): kota karsiligi izletilir.
 * Odul kazanilirsa true; yarim birakilirsa/yuklenemezse false.
 * Web ortaminda reklam yok; akisi bozmamak icin true doner.
 */
export async function showRewardInterstitialAd(): Promise<boolean> {
  if (!adsAvailable()) return true

  try {
    await initAds()
    await AdMob.prepareRewardInterstitialAd({ adId: AD_IDS.rewardInterstitial })
    await AdMob.showRewardInterstitialAd()
    return true
  } catch (e) {
    console.warn('Odullu gecis reklami gosterilemedi', e)
    return false
  }
}

// --- Uygulama acilis reklami (App Open) ---
// Ilk acilista + on plana donuslerde gosterilir; iki gosterim arasi
// en az APP_OPEN_MIN_GAP_MS bekler (bogmamak icin).
const APP_OPEN_MIN_GAP_MS = 120_000
const LS_APP_OPEN_AT = 'hng-ad-appopen-at'

async function loadAppOpenAd(): Promise<boolean> {
  try {
    await initAds()
    await AdMob.loadAppOpen({ adId: AD_IDS.appOpen })
    return true
  } catch (e) {
    console.warn('App Open yuklenemedi', e)
    return false
  }
}

/**
 * Yuklu App Open reklamini gosterir (yoksa once yuklemeyi dener).
 * Sikligi kisitlidir; gosterilemezse sessizce gecilir.
 */
export async function showAppOpenAd(): Promise<void> {
  if (!adsAvailable()) return
  if (Date.now() - lsGet(LS_APP_OPEN_AT) < APP_OPEN_MIN_GAP_MS) return

  try {
    await initAds()
    const { value: loaded } = await AdMob.isAppOpenLoaded().catch(() => ({ value: false }))
    if (!loaded) {
      const ok = await loadAppOpenAd()
      if (!ok) return
    }
    await AdMob.showAppOpen()
    lsSet(LS_APP_OPEN_AT, Date.now())
    // Sonraki gosterim icin arka planda yenisini hazirla
    loadAppOpenAd().catch(() => {})
  } catch (e) {
    console.warn('App Open gosterilemedi', e)
  }
}

// --- Araya giren reklam (interstitial) ---
// Katman bazli siklik: free -> her rota aramasinda, lite -> her 3'te bir,
// premium -> hicbir zaman. Ilk arama asla reklam cikarmaz; iki reklam
// arasi en az INTERSTITIAL_MIN_GAP_MS bekler (bogmamak icin).
const INTERSTITIAL_EVERY: Record<'free' | 'lite' | 'premium', number> = {
  free: 1,
  lite: 3,
  premium: Number.POSITIVE_INFINITY,
}
const INTERSTITIAL_MIN_GAP_MS = 45_000
const LS_SEARCH_COUNT = 'hng-ad-search-count'
const LS_LAST_SHOWN = 'hng-ad-interstitial-at'

function lsGet(key: string): number {
  try {
    return Number(localStorage.getItem(key) ?? 0) || 0
  } catch {
    return 0
  }
}

function lsSet(key: string, value: number): void {
  try {
    localStorage.setItem(key, String(value))
  } catch {
    // localStorage kapaliysa sessizce gec
  }
}

/**
 * Rota aramasi basariyla bitince cagrilir. Uyelik katmanina gore sira
 * geldiyse araya giren reklami gosterir. Hata olursa sessizce gecer.
 */
export async function maybeShowInterstitial(tier: 'free' | 'lite' | 'premium' = 'free'): Promise<void> {
  if (!adsAvailable() || !AD_IDS.interstitial) return
  if (tier === 'premium') return

  const count = lsGet(LS_SEARCH_COUNT) + 1
  lsSet(LS_SEARCH_COUNT, count)

  const every = INTERSTITIAL_EVERY[tier] ?? 1

  // Ilk arama ve tekrar araliginda reklam yok
  if (count === 1 || count % every !== 0) return
  if (Date.now() - lsGet(LS_LAST_SHOWN) < INTERSTITIAL_MIN_GAP_MS) return

  try {
    await initAds()
    await AdMob.prepareInterstitial({ adId: AD_IDS.interstitial })
    await AdMob.showInterstitial()
    lsSet(LS_LAST_SHOWN, Date.now())
  } catch (e) {
    console.warn('Interstitial gosterilemedi', e)
  }
}
