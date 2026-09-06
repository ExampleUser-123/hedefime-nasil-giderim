import { useState } from 'react'
import {
  clearHistory,
  getHistory,
  getSaved,
  removeSaved,
  type SavedRoute,
} from '@/lib/storage'
import { IconBell, IconClock, IconStar, IconUser } from '@/icons'

const MODE_LABELS: Record<string, string> = {
  otobus: 'Otobüs',
  metro: 'Metro',
  deniz: 'Deniz',
  arac: 'Araba',
  motosiklet: 'Motosiklet',
  ucak: 'Uçak',
  tren: 'Tren',
  yuruyus: 'Yürüyüş',
}

export function RouteListRow({
  entry,
  onOpen,
  onRemove,
}: {
  entry: SavedRoute
  onOpen: () => void
  onRemove?: () => void
}) {
  const short = (place: string) => place.split(',').slice(0, 1).join('').trim() || place

  return (
    <div className="flex items-center gap-2 rounded-2xl border border-line bg-surface-2/90 p-3">
      <button
        type="button"
        onClick={onOpen}
        className="min-w-0 flex-1 text-left"
      >
        <p className="truncate text-sm font-bold">
          {short(entry.from)}
          <span className="mx-1.5 text-accent">→</span>
          {short(entry.to)}
        </p>
        <p className="mt-0.5 text-xs text-muted">
          {MODE_LABELS[entry.mode] ?? entry.mode}
          {entry.people > 1 && ` · ${entry.people} kişi`}
        </p>
      </button>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label="Listeden çıkar"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-muted transition-colors hover:text-red-300"
        >
          ×
        </button>
      )}
    </div>
  )
}

export function SavedScreen({ onOpenRoute }: { onOpenRoute: (entry: SavedRoute) => void }) {
  const [saved, setSaved] = useState(() => getSaved())

  return (
    <ScreenShell title="Kayıtlılar" icon={<IconStar className="h-5 w-5" />}>
      {saved.length === 0 ? (
        <EmptyState text="Henüz kaydedilmiş rota yok. Arama sonuçlarındaki yıldıza dokunarak rotanı kaydedebilirsin." />
      ) : (
        <div className="space-y-2.5">
          {saved.map((entry) => (
            <RouteListRow
              key={`${entry.from}-${entry.to}`}
              entry={entry}
              onOpen={() => onOpenRoute(entry)}
              onRemove={() => {
                removeSaved(entry.from, entry.to)
                setSaved(getSaved())
              }}
            />
          ))}
        </div>
      )}
    </ScreenShell>
  )
}

export function HistoryScreen({ onOpenRoute }: { onOpenRoute: (entry: SavedRoute) => void }) {
  const [history, setHistory] = useState(() => getHistory())

  return (
    <ScreenShell title="Geçmiş" icon={<IconClock className="h-5 w-5" />}>
      {history.length === 0 ? (
        <EmptyState text="Henüz arama geçmişin yok. Yaptığın aramalar burada birikecek." />
      ) : (
        <>
          <div className="space-y-2.5">
            {history.map((entry) => (
              <RouteListRow
                key={`${entry.from}-${entry.to}-${entry.savedAt}`}
                entry={entry}
                onOpen={() => onOpenRoute(entry)}
              />
            ))}
          </div>
          <button
            type="button"
            onClick={() => {
              clearHistory()
              setHistory([])
            }}
            className="mt-4 w-full rounded-xl border border-line py-2.5 text-xs font-bold text-muted transition-colors hover:border-red-400/50 hover:text-red-300"
          >
            Geçmişi temizle
          </button>
        </>
      )}
    </ScreenShell>
  )
}

export function NotificationsScreen() {
  return (
    <ScreenShell title="Bildirimler" icon={<IconBell className="h-5 w-5" />}>
      <EmptyState text="Bildirimler yakında! Fiyat düşüşleri ve sefer hatırlatıcıları burada olacak." />
    </ScreenShell>
  )
}

export function ProfileScreen({ defaultVehicle }: { defaultVehicle: string | null }) {
  return (
    <ScreenShell title="Profil" icon={<IconUser className="h-5 w-5" />}>
      <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
        <p className="text-xs uppercase tracking-wide text-muted">Varsayılan araç</p>
        <p className="mt-1 text-sm font-bold">{defaultVehicle ?? 'Araba/Motosiklet modunda seçilmedi'}</p>
        <p className="mt-1 text-xs text-muted">
          Araba veya Motosiklet modunda "Hatırla" işaretlersen buradaki araç her seferinde kullanılır.
        </p>
      </div>

      <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
        <p className="text-xs uppercase tracking-wide text-muted">Veri kaynakları</p>
        <ul className="mt-2 space-y-1 text-xs text-muted">
          <li>· İstanbul İETT (canlı rota) · İzmir ESHOT · İzdeniz</li>
          <li>· Kocaeli, Konya belediye GTFS verileri</li>
          <li>· Antalya, Adana, Gaziantep, Muğla, Sivas</li>
          <li>· Düzce, Erzurum, Ordu, Zonguldak, Samsun</li>
          <li>· Çanakkale, Edirne (KentKart)</li>
          <li>· OSRM rota · Open-Meteo hava durumu</li>
          <li>· Uçak ve tren fiyatları mesafe bazlı tahminidir</li>
        </ul>
      </div>

      <p className="mt-4 text-center text-xs text-muted">
        Hedefime Nasıl Giderim · v1.0
      </p>
    </ScreenShell>
  )
}

function ScreenShell({
  title,
  icon,
  children,
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="relative z-10 mx-auto w-full max-w-xl px-4 pb-28 pt-6 sm:px-6">
      <div className="flex items-center gap-2.5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 text-accent">
          {icon}
        </span>
        <h1 className="text-xl font-bold">{title}</h1>
      </div>
      <div className="mt-5">{children}</div>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <p className="rounded-2xl border border-line bg-surface-2/90 px-4 py-6 text-center text-sm text-muted">
      {text}
    </p>
  )
}
