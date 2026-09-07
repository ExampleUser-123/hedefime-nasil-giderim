import { Capacitor } from '@capacitor/core'
import {
  AdMob,
  BannerAdPosition,
  BannerAdSize,
  MaxAdContentRating,
  type BannerAdOptions,
} from '@capacitor-community/admob'

// Google'in herkese acik TEST reklam ID'leri — gercek reklam goruntulemez,
// hesap ucretlendirilmez. AdMob hesabi acilinca asagidaki ID'ler
// para-kazanma-planindaki gercek ID'lerle degistirilecek.
const TEST_AD_IDS = {
  banner: 'ca-app-pub-3940256099942544/6300978111',
  rewarded: 'ca-app-pub-3940256099942544/5224354917',
}

let initialized = false

export function adsAvailable(): boolean {
  return Capacitor.isNativePlatform()
}

export async function initAds(): Promise<void> {
  if (!adsAvailable() || initialized) return

  try {
    await AdMob.initialize({
      initializeForTesting: true,
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
      adId: TEST_AD_IDS.banner,
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
    await AdMob.prepareRewardVideoAd({ adId: TEST_AD_IDS.rewarded })
    await AdMob.showRewardVideoAd()
    return true
  } catch (e) {
    console.warn('Odullu reklam gosterilemedi', e)
    return false
  }
}
