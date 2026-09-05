import { useState } from 'react'
import { motion, MotionConfig } from 'framer-motion'
import WeatherChip from '@/components/WeatherChip'
import RouteSearch, { type SearchPreset } from '@/components/RouteSearch'
import ChatDrawer from '@/components/ChatDrawer'
import MapView from '@/components/MapView'
import BottomNav, { type Tab } from '@/components/BottomNav'
import {
  HistoryScreen,
  NotificationsScreen,
  ProfileScreen,
  SavedScreen,
} from '@/components/TabScreens'
import { IconLogo } from '@/icons'
import type { PlanResult } from '@/lib/api'

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
  const [mode, setMode] = useState<SearchPreset['mode']>('otobus')
  const [routeIndex, setRouteIndex] = useState(0)
  const [preset, setPreset] = useState<SearchPreset | null>(null)

  function handlePlanChange(nextPlan: PlanResult | null) {
    setPlan(nextPlan)
    setRouteIndex(0)
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

              <WeatherChip />
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
                />
              </div>
            </motion.section>
          </>
        )}

        {tab === 'saved' && <SavedScreen onOpenRoute={openRoute} />}
        {tab === 'history' && <HistoryScreen onOpenRoute={openRoute} />}
        {tab === 'alerts' && <NotificationsScreen />}
        {tab === 'profile' && <ProfileScreen defaultVehicle={defaultVehicleName()} />}

        <BottomNav
          active={tab}
          onChange={setTab}
          onAi={() => setChatOpen(true)}
        />

        <ChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </main>
    </MotionConfig>
  )
}
