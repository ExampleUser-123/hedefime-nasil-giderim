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
import {
  HistoryScreen,
  NotificationsScreen,
  ProfileScreen,
  SavedScreen,
} from '@/components/TabScreens'
import { IconLogo } from '@/icons'
import type { AuthUser, PlanResult } from '@/lib/api'
import { getStoredUser, refreshAuthState, signOut } from '@/lib/auth'
import { rescheduleAll } from '@/lib/reminders'

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

  // Gecmis sefer hatirlaticlarini temizle, gelecektekileri yeniden planla
  useEffect(() => {
    rescheduleAll().catch(() => {})
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

  const isHome = tab === 'home'

  return (
    <MotionConfig reducedMotion="user">
      <main className="relative flex min-h-dvh flex-col overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
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

            <div className="relative z-10 flex-1" aria-hidden="true" />

            <motion.section
              aria-label="Rota planlama"
              initial={{ y: 60, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="relative z-10 mx-auto w-full max-w-xl px-4 pb-24 sm:px-6"
            >
              <div className="rounded-3xl border border-line bg-surface/85 p-5 shadow-2xl shadow-black/40 backdrop-blur-md sm:p-6">
                <RouteSearch
                  mode={mode}
                  onModeChange={setMode}
                  plan={plan}
                  onPlanChange={handlePlanChange}
                  preset={preset}
                  routeIndex={routeIndex}
                  onRouteIndexChange={setRouteIndex}
                  onRequireLogin={openLogin}
                />
              </div>
            </motion.section>
          </>
        )}

        {tab === 'stops' && <NearbyStops />}
        {tab === 'saved' && <SavedScreen onOpenRoute={openRoute} />}
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
