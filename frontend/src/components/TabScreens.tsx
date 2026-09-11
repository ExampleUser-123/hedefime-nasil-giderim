import { useEffect, useState } from 'react'
import { API_BASE, fetchUsage, reverseGeocode, type AuthUser, type UsageInfo } from '@/lib/api'
import {
  clearHistory,
  getHistory,
  getPinnedPlace,
  setPinnedPlace,
  clearPinnedPlace,
  type SavedRoute,
} from '@/lib/storage'
import {
  loadFavorites,
  toggleFavorite,
  type FavoriteView,
} from '@/lib/favorites'
import { signOut } from '@/lib/auth'
import UpgradeSheet from '@/components/UpgradeSheet'
import { IconBell, IconClock, IconStar, IconUser } from '@/icons'

const MODE_LABELS: Record<string, string> = {
  tumu: 'Tümü',
  otobus: 'Otobüs',
  metro: 'Metro',
  tramvay: 'Tramvay',
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
  entry: { from: string; to: string; people: number; mode: string }
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

export function SavedScreen({
  onOpenRoute,
}: {
  onOpenRoute: (entry: { from: string; to: string; people: number; mode: string }) => void
}) {
  const [items, setItems] = useState<FavoriteView[] | null>(null)

  useEffect(() => {
    let cancelled = false

    loadFavorites()
      .then(({ items: favorites }) => {
        if (!cancelled) setItems(favorites)
      })
      .catch(() => {
        if (!cancelled) setItems([])
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <ScreenShell title="Kayıtlılar" icon={<IconStar className="h-5 w-5" />}>
      {items === null ? (
        <EmptyState text="Kayıtlı rotalar yükleniyor…" />
      ) : items.length === 0 ? (
        <EmptyState text="Henüz kaydedilmiş rota yok. Arama sonuçlarındaki yıldıza dokunarak rotanı kaydedebilirsin." />
      ) : (
        <div className="space-y-2.5">
          {items.map((entry) => (
            <RouteListRow
              key={entry.id ?? `${entry.from}-${entry.to}`}
              entry={entry}
              onOpen={() => onOpenRoute(entry)}
              onRemove={async () => {
                const result = await toggleFavorite({
                  from: entry.from,
                  to: entry.to,
                  people: entry.people,
                  mode: entry.mode,
                })

                if (result.items) setItems(result.items)
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
  const [serverUp, setServerUp] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false

    fetch(`${API_BASE}/`)
      .then((res) => {
        if (!cancelled) setServerUp(res.ok)
      })
      .catch(() => {
        if (!cancelled) setServerUp(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <ScreenShell title="Bildirimler" icon={<IconBell className="h-5 w-5" />}>
      <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
        <p className="text-xs uppercase tracking-wide text-muted">Sunucu durumu</p>
        <div className="mt-2 flex items-center gap-2">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              serverUp === null
                ? 'bg-amber-400 animate-pulse'
                : serverUp
                  ? 'bg-emerald-400'
                  : 'bg-red-400'
            }`}
          />
          <p className="text-sm font-bold">
            {serverUp === null
              ? 'Kontrol ediliyor…'
              : serverUp
                ? 'Sunucu çalışıyor, rota araması hazır'
                : 'Sunucuya ulaşılamıyor — internet bağlantını kontrol et'}
          </p>
        </div>
      </div>

      <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
        <p className="text-xs uppercase tracking-wide text-muted">İpuçları</p>
        <ul className="mt-2 space-y-2 text-xs text-muted">
          <li>· Rota sonuçlarındaki yıldıza dokunarak rotanı kaydedebilirsin.</li>
          <li>· Araba/Motosiklet modunda "Hatırla" işaretlersen aracın her seferinde seçilir.</li>
          <li>· Metro, Tramvay ve Deniz modlarında sadece o türde rotalar listelenir; "Tümünü göster" ile hepsini görebilirsin.</li>
          <li>· 38 ilde şehir içi toplu taşıma, tüm Türkiye'de araç/uçak/tren hesaplaması mevcut.</li>
          <li>· AI asistanına "Yarın 4 kişi İzmit'ten İzmir'e en ucuz nasıl gideriz?" gibi doğal sorular sorabilirsin.</li>
          <li>· Sesli rehberlik ve yolculuk raporu</li>
          <li>· Yürüyüş toleransı seçimi</li>
        </ul>
      </div>
    </ScreenShell>
  )
}

export function ProfileScreen({
  defaultVehicle,
  user,
  onRequireLogin,
  onLogout,
}: {
  defaultVehicle: string | null
  user: AuthUser | null
  onRequireLogin: () => void
  onLogout: () => void
}) {
  const [homePlace, setHomePlace] = useState(() => getPinnedPlace('home'))
  const [workPlace, setWorkPlace] = useState(() => getPinnedPlace('work'))
  const [pinning, setPinning] = useState<'home' | 'work' | null>(null)
  const [pinError, setPinError] = useState<string | null>(null)
  const [usage, setUsage] = useState<UsageInfo | null>(null)
  const [upgradeOpen, setUpgradeOpen] = useState(false)

  useEffect(() => {
    let alive = true
    fetchUsage()
      .then((u) => {
        if (alive) setUsage(u)
      })
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [user?.id])

  function captureLocation(kind: 'home' | 'work') {
    if (pinning) return

    if (!('geolocation' in navigator)) {
      setPinError('Cihazın konum desteği sunmuyor.')
      return
    }

    setPinning(kind)
    setPinError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords
          let address = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`

          try {
            const place = await reverseGeocode(latitude, longitude)
            address = place.display_name.split(',').slice(0, 3).join(',')
          } catch {
            // adres bulunamazsa koordinat etiketi yeterli
          }

          const next = { label: kind === 'home' ? 'Ev' : 'İş', address, lat: latitude, lon: longitude }
          setPinnedPlace(kind, next)

          if (kind === 'home') setHomePlace(next)
          else setWorkPlace(next)
        } finally {
          setPinning(null)
        }
      },
      () => {
        setPinning(null)
        setPinError('Konum alınamadı. GPS iznini kontrol et.')
      },
      { enableHighAccuracy: true, timeout: 12000 },
    )
  }

  function pinnedRow(kind: 'home' | 'work') {
    const place = kind === 'home' ? homePlace : workPlace
    const icon = kind === 'home' ? '🏠' : '💼'
    const title = kind === 'home' ? 'Ev konumu' : 'İş konumu'

    return (
      <div className="flex items-center gap-3 py-2.5">
        <span aria-hidden="true" className="text-lg">{icon}</span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold">{title}</p>
          <p className="truncate text-xs text-muted">
            {place ? place.address : 'Henüz ayarlanmadı'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => captureLocation(kind)}
          disabled={pinning !== null}
          className="shrink-0 rounded-lg border border-line px-3 py-1.5 text-xs font-bold text-accent disabled:opacity-40"
        >
          {pinning === kind ? 'Alınıyor…' : place ? 'Güncelle' : 'Konumumla ayarla'}
        </button>
        {place && (
          <button
            type="button"
            onClick={() => {
              clearPinnedPlace(kind)
              if (kind === 'home') setHomePlace(null)
              else setWorkPlace(null)
            }}
            aria-label={`${title} temizle`}
            className="shrink-0 text-xs text-muted transition-colors hover:text-red-300"
          >
            ✕
          </button>
        )}
      </div>
    )
  }

  return (
    <ScreenShell title="Profil" icon={<IconUser className="h-5 w-5" />}>
      {user ? (
        <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
          <div className="flex items-center gap-3">
            {user.picture ? (
              <img
                src={user.picture}
                alt=""
                className="h-12 w-12 rounded-full border border-line"
                referrerPolicy="no-referrer"
              />
            ) : (
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent/15 text-lg font-bold text-accent">
                {(user.name ?? 'K').slice(0, 1).toUpperCase()}
              </span>
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-bold">{user.name ?? 'Kullanıcı'}</p>
              <p className="truncate text-xs text-muted">{user.email}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={async () => {
              await signOut()
              onLogout()
            }}
            className="mt-4 w-full rounded-xl border border-line py-2.5 text-xs font-bold text-muted transition-colors hover:border-red-400/50 hover:text-red-300"
          >
            Çıkış yap
          </button>
        </div>
      ) : (
        <div className="rounded-2xl border border-line bg-surface-2/90 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Hesap</p>
          <p className="mt-1 text-sm font-bold">Google ile giriş yap</p>
          <p className="mt-1 text-xs text-muted">
            Favori rotaların hesabına kaydedilir, telefonda kalmaz. AI asistanı
            da hesapla kullanılır.
          </p>
          <button
            type="button"
            onClick={onRequireLogin}
            className="mt-3 w-full rounded-xl bg-accent py-2.5 text-sm font-bold text-accent-ink"
          >
            Google ile giriş yap
          </button>
        </div>
      )}

      <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs uppercase tracking-wide text-muted">Üyelik</p>
          {usage && (
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
              usage.tier === 'premium'
                ? 'bg-amber-400/20 text-amber-300'
                : usage.tier === 'lite'
                  ? 'bg-teal-400/20 text-teal-300'
                  : 'bg-white/10 text-muted'
            }`}>
              {usage.tier === 'premium' ? 'PREMIUM' : usage.tier === 'lite' ? 'LITE' : 'ÜCRETSİZ'}
            </span>
          )}
        </div>
        {usage && (
          <p className="mt-1.5 text-xs text-muted">
            Bugün {usage.routes_used}
            {usage.routes_limit >= 0 ? `/${usage.routes_limit}` : ''} rota ·{' '}
            {usage.ai_used}
            {usage.ai_limit >= 0 ? `/${usage.ai_limit}` : ''} AI mesajı
          </p>
        )}
        {usage?.tier !== 'premium' && (
          <button
            type="button"
            onClick={() => setUpgradeOpen(true)}
            className="mt-3 w-full rounded-xl bg-teal-400 py-2.5 text-sm font-bold text-slate-900 active:scale-[0.99]"
          >
            Planları gör → Daha fazla rota, reklamsız
          </button>
        )}
      </div>

      {upgradeOpen && <UpgradeSheet onClose={() => setUpgradeOpen(false)} />}

      <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
        <p className="text-xs uppercase tracking-wide text-muted">Sabit konumlar</p>
        <p className="mt-1 text-xs text-muted">
          Ev ve İş konumlarını bir kez ayarla; arama kutusuna dokunduğunda hazır çıkar.
        </p>
        <div className="mt-1 divide-y divide-line/60">
          {pinnedRow('home')}
          {pinnedRow('work')}
        </div>
        {pinError && (
          <p role="alert" className="mt-2 text-xs text-red-300">{pinError}</p>
        )}
      </div>

      <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
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
