import type { ReactElement } from 'react'
import {
  IconBell,
  IconClock,
  IconHome,
  IconSparkle,
  IconStar,
  IconUser,
} from '@/icons'

export type Tab = 'home' | 'saved' | 'history' | 'alerts' | 'profile'

type TabItem = { id: Tab; label: string; icon: (props: { className?: string }) => ReactElement }

const TABS: TabItem[] = [
  { id: 'home', label: 'Ana Sayfa', icon: IconHome },
  { id: 'saved', label: 'Kayıtlılar', icon: IconStar },
  { id: 'history', label: 'Geçmiş', icon: IconClock },
]

const AFTER_TABS: TabItem[] = [
  { id: 'alerts', label: 'Bildirimler', icon: IconBell },
  { id: 'profile', label: 'Profil', icon: IconUser },
]

export default function BottomNav({
  active,
  onChange,
  onAi,
}: {
  active: Tab
  onChange: (tab: Tab) => void
  onAi: () => void
}) {
  function renderTab({ id, label, icon: Icon }: TabItem) {
    const isActive = active === id

    return (
      <button
        key={id}
        type="button"
        onClick={() => onChange(id)}
        aria-current={isActive ? 'page' : undefined}
        className={`flex min-h-[56px] flex-1 flex-col items-center justify-center gap-0.5 px-1 py-2 text-[10px] font-bold transition-colors ${
          isActive ? 'text-accent' : 'text-muted hover:text-fg'
        }`}
      >
        <Icon className="h-5 w-5" />
        <span>{label}</span>
        <span
          className={`h-0.5 w-6 rounded-full transition-colors ${
            isActive ? 'bg-accent' : 'bg-transparent'
          }`}
          aria-hidden="true"
        />
      </button>
    )
  }

  return (
    <nav
      aria-label="Ana menü"
      className="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-xl items-stretch justify-around px-2">
        {TABS.map(renderTab)}

        <button
          type="button"
          onClick={onAi}
          aria-label="AI asistan sohbetini aç"
          className="flex min-h-[56px] flex-1 flex-col items-center justify-center gap-0.5 px-1 py-2 text-[10px] font-bold text-accent transition-colors hover:text-accent"
        >
          <IconSparkle className="h-6 w-6" />
          <span>AI</span>
        </button>

        {AFTER_TABS.map(renderTab)}
      </div>
    </nav>
  )
}
