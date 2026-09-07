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
