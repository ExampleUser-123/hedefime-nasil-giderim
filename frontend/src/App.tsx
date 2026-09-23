import { useEffect, useState } from 'react'
import { Capacitor, type PluginListenerHandle } from '@capacitor/core'
import { App as CapacitorApp } from '@capacitor/app'
import { AnimatePresence, motion, MotionConfig } from 'framer-motion'
import splashArtwork from '@/assets/splash.png'
import WeatherChip from '@/components/WeatherChip'
import RouteSearch, { type SearchPreset } from '@/components/RouteSearch'
import ChatDrawer from '@/components/ChatDrawer'
import LoginSheet from '@/components/LoginSheet'
import MapView from '@/components/MapView'
import BottomNav, { type Tab } from '@/components/BottomNav'
import NearbyStops from '@/components/NearbyStops'
import VibeCard from '@/components/VibeCard'
import MagicShare from '@/components/MagicShare'
import NightCard from '@/components/NightCard'
import TargetsSection from '@/components/TargetsSection'
import MarketplaceScreen from '@/components/MarketplaceScreen'
import {
  HistoryScreen,
  NotificationsScreen,
  ProfileScreen,
  SavedScreen,
} from '@/components/TabScreens'
import { IconLogo } from '@/icons'
import type { AuthUser, PlanResult, RouteIntent } from '@/lib/api'
import { fetchShareRoute } from '@/lib/api'
import { AUTH_CHANGED_EVENT, getStoredUser, refreshAuthState, signOut } from '@/lib/auth'
import { INVITE_CODE_KEY } from '@/lib/auth'
import { getPinnedPlace } from '@/lib/storage'
import { goToPlace } from '@/lib/navigate'
import { rescheduleAll } from '@/lib/reminders'
import { initShareListener } from '@/lib/shareIntent'

function defaultVehicleName(): string | null {
  try {
    return localStorage.getItem('hng-vehicle-name')
  } catch {
    return null
  }
}

export default function App() {
  const [tab, setTab] = useState<Tab>('home')
  const [chatOpen, setChatOpen] = useState(false)
  const [plan, setPlan] = useState<PlanResult | null>(null)
  const [mode, setMode] = useState<SearchPreset['mode']>('tumu')
  const [routeIndex, setRouteIndex] = useState(0)
  const [preset, setPreset] = useState<SearchPreset | null>(null)
  const [bootSplash, setBootSplash] = useState(true)
  const [weatherCity, setWeatherCity] = useState('İstanbul')
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => getStoredUser())
  const [loginOpen, setLoginOpen] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setBootSplash(false), 1400)
    return () => clearTimeout(timer)
  }, [])

  // Suresi dolmus oturum varsa temizle
  useEffect(() => {
    refreshAuthState().then(() => setAuthUser(getStoredUser())).catch(() => {})
  }, [])

  // Web'de Google redirect akisiyla giris: oturum acilinca arayuz guncellensin
  useEffect(() => {
    const onAuthChanged = () => setAuthUser(getStoredUser())
    window.addEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
    return () => window.removeEventListener(AUTH_CHANGED_EVENT, onAuthChanged)
  }, [])

  // Gecmis sefer hatirlaticlarini temizle, gelecektekileri yeniden planla
  useEffect(() => {
    rescheduleAll().catch(() => {})
  }, [])

  // Native paylasim: baska uygulamadan gelen metni karsila (Magic Share)
  useEffect(() => {
    initShareListener()
  }, [])

  // Widget kisayollari: hng://go?target=home|work -> sabit konuma rota
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return
    let handle: PluginListenerHandle | null = null
    CapacitorApp.addListener('appUrlOpen', (event: { url: string }) => {
      try {
        const u = new URL(event.url)
        if (u.protocol !== 'hng:' || u.host !== 'go') return
        const target = u.searchParams.get('target')
        if (target !== 'home' && target !== 'work') return
        const place = getPinnedPlace(target)
        setTab('home')
        if (!place) return
        void goToPlace(place.address, openRoute).catch(() => {})
      } catch {
        // bozuk link: normal acilis
      }
    }).then((h) => {
      handle = h
    }).catch(() => {})
    return () => {
      handle?.remove()
    }
  }, [])

  // Davet linki: ?ref=KOD ile gelinirse kayit sirasinda kullanilmak uzere sakla
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const ref = (params.get('ref') || '').trim()
    if (!ref) return
    try {
      localStorage.setItem(INVITE_CODE_KEY, ref.slice(0, 16))
    } catch {
      // sessizce gec
    }
    params.delete('ref')
    const rest = params.toString()
    window.history.replaceState({}, '', window.location.pathname + (rest ? `?${rest}` : ''))
  }, [])

  // Paylasilan rota linki: ?share=ID ile acilirsa rotayi otomatik doldur
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const shareId = params.get('share')
    if (!shareId) return

    // Adres cubugunu temizle (link tekrar tetiklenmesin)
    window.history.replaceState({}, '', window.location.pathname)

    fetchShareRoute(shareId)
      .then((rec) => {
        setTab('home')
        setPreset({
          from: rec.start,
          to: rec.destination,
          people: rec.people,
          mode: rec.mode as SearchPreset['mode'],
          key: Date.now(),
        })
      })
      .catch(() => {
        // gecersiz/sure dolmus link: normal acilis
      })
  }, [])

  function openLogin() {
    setLoginOpen(true)
  }

  async function handleLogout() {
    await signOut()
    setAuthUser(null)
  }

  // Android geri tusu: once acik ekrani kapat, ana sayfadaysa uygulamadan cik
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return

    let handler: PluginListenerHandle | null = null

    CapacitorApp.addListener('backButton', () => {
      if (chatOpen) {
        setChatOpen(false)
        return
      }
      if (plan) {
        setPlan(null)
        setRouteIndex(0)
        return
      }
      if (tab !== 'home') {
        setTab('home')
        return
      }
      CapacitorApp.exitApp()
    }).then((h) => {
      handler = h
    })

    return () => {
      handler?.remove()
    }
  }, [chatOpen, plan, tab])

  function handlePlanChange(nextPlan: PlanResult | null) {
    setPlan(nextPlan)
    setRouteIndex(0)

    if (nextPlan?.start) {
      // "Taksim, Beyoğlu, İstanbul" -> "İstanbul"; zaten şehirse aynen kullan
      const parts = nextPlan.start.split(',')
      const city = parts[parts.length - 1].trim()
      if (city) setWeatherCity(city)
    }
  }

  function openRoute(entry: { from: string; to: string; people: number; mode: string }) {
    setPlan(null)
    setTab('home')
    setPreset({
      from: entry.from,
      to: entry.to,
      people: entry.people,
      mode: entry.mode as SearchPreset['mode'],
      key: Date.now(),
    })
  }

  // AI asistanindan gelen rota niyetini arama formuna dok
  function handlePlanIntent(intent: RouteIntent) {
    if (!intent.start || !intent.end) return

    openRoute({
      from: intent.start,
      to: intent.end,
      people: intent.people > 0 ? intent.people : 1,
      mode: intent.mode ?? 'tumu',
    })
  }

  const isHome = tab === 'home'

  return (
    <MotionConfig reducedMotion="user">
      <main className="relative flex min-h-dvh flex-col overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/hero-map-background.png)' }}
          aria-hidden="true"
        />

        {isHome && plan && <MapView plan={plan} mode={mode} routeIndex={routeIndex} />}

        {!isHome && (
          <div className="absolute inset-0 bg-bg/95" aria-hidden="true" />
        )}

        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-bg/30 via-transparent to-bg/70" aria-hidden="true" />

        {isHome && (
          <>
            <header className="relative z-10 flex items-center justify-between px-5 pt-5 sm:px-8">
              <div className="flex items-center gap-2.5">
                <IconLogo className="h-8 w-8" />
                <span className="font-display text-[15px] font-bold uppercase tracking-[0.08em]">
                  Hedefime Nasıl Giderim
                </span>
              </div>

              <WeatherChip city={weatherCity} />
            </header>

            {/* Esnek bosluk: tiklamalari haritaya gecirir (harita etkilesimini oldurmesin) */}
            <div className="pointer-events-none relative z-10 flex-1" aria-hidden="true" />

            <motion.section
              aria-label="Rota planlama"
              initial={{ y: 60, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className={`relative z-10 mx-auto w-full max-w-xl px-4 pb-24 sm:px-6 ${plan ? 'pointer-events-none' : ''}`}
            >
              <div className={plan ? 'contents' : 'rounded-3xl border border-line bg-surface/85 p-5 shadow-2xl shadow-black/40 backdrop-blur-md sm:p-6'}>
                <RouteSearch
                  mode={mode}
                  onModeChange={setMode}
                  plan={plan}
                  onPlanChange={handlePlanChange}
                  preset={preset}
                  routeIndex={routeIndex}
                  onRouteIndexChange={setRouteIndex}
                  onRequireLogin={openLogin}
                  city={weatherCity}
                />
              </div>
              {/* Rota acikken sonuclar bottom sheet'tedir; alt kartlar gizlenir, harita tam gorunur */}
              {!plan && (
              <>
              <VibeCard plan={plan} city={weatherCity} />
              <MagicShare onOpenRoute={openRoute} />
              <NightCard onOpenRoute={openRoute} />
              </>
              )}
            </motion.section>
          </>
        )}

        {tab === 'stops' && <NearbyStops />}
        {tab === 'explore' && <MarketplaceScreen onOpenRoute={openRoute} />}
        {tab === 'saved' && (
          <>
            <TargetsSection onOpenRoute={openRoute} />
            <SavedScreen onOpenRoute={openRoute} />
          </>
        )}
        {tab === 'history' && <HistoryScreen onOpenRoute={openRoute} />}
        {tab === 'alerts' && <NotificationsScreen />}
        {tab === 'profile' && (
          <ProfileScreen
            defaultVehicle={defaultVehicleName()}
            user={authUser}
            onRequireLogin={openLogin}
            onLogout={handleLogout}
          />
        )}

        <BottomNav
          active={tab}
          onChange={setTab}
          onAi={() => setChatOpen(true)}
        />

        <ChatDrawer
          open={chatOpen}
          onClose={() => setChatOpen(false)}
          onRequireLogin={openLogin}
          authOk={!!authUser}
          onPlanIntent={handlePlanIntent}
        />

        <LoginSheet
          open={loginOpen}
          onClose={() => setLoginOpen(false)}
          onLoggedIn={() => setAuthUser(getStoredUser())}
        />

        <AnimatePresence>
          {bootSplash && (
            <motion.div
              key="boot-splash"
              className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#00091B]"
              initial={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.45, ease: 'easeOut' }}
            >
              <motion.img
                src={splashArtwork}
                alt="Hedefime Nasıl Giderim"
                className="w-[72%] max-w-sm"
                initial={{ scale: 0.94, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </MotionConfig>
  )
}
