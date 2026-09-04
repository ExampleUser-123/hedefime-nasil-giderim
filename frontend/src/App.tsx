import { useState } from 'react'
import { motion, MotionConfig } from 'framer-motion'
import WeatherChip from '@/components/WeatherChip'
import RouteSearch from '@/components/RouteSearch'
import AiBanner from '@/components/AiBanner'
import ChatDrawer from '@/components/ChatDrawer'
import { IconLogo } from '@/icons'

export default function App() {
  const [chatOpen, setChatOpen] = useState(false)

  return (
    <MotionConfig reducedMotion="user">
      <main className="relative flex min-h-dvh flex-col overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: 'url(/hero-map-background.png)' }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-bg/40 via-bg/20 to-bg/80" aria-hidden="true" />

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
          className="relative z-10 mx-auto w-full max-w-xl px-4 pb-6 sm:px-6"
        >
          <div className="rounded-3xl border border-line bg-surface/85 p-5 shadow-2xl shadow-black/40 backdrop-blur-md sm:p-6">
            <RouteSearch />

            <div className="mt-4">
              <AiBanner onOpen={() => setChatOpen(true)} />
            </div>
          </div>

          <p className="mt-4 text-center text-xs text-muted">
            Rotalar OSRM ve İETT verileriyle hesaplanır · Hava durumu Open-Meteo
          </p>
        </motion.section>

        <ChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
      </main>
    </MotionConfig>
  )
}
