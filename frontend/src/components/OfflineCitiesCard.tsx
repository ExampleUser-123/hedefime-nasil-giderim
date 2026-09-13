import { useEffect, useState, type ReactElement } from 'react'
import { fetchTransitDataCity } from '@/lib/api'
import {
  listOfflineCities,
  saveOfflineCity,
  removeOfflineCity,
  type OfflineCity,
} from '@/lib/offlineStorage'

// Backend slug -> gosterim adi ( Turkce buyuk harf )
function displayName(slug: string): string {
  const special: Record<string, string> = {
    afyon: 'Afyonkarahisar',
    balikesir: 'Balıkesir',
    diyarbakir: 'Diyarbakır',
    isparta: 'Isparta',
    kahramanmaras: 'Kahramanmaraş',
    kastamonu: 'Kastamonu',
    kocaeli: 'Kocaeli',
    konya: 'Konya',
    malatya: 'Malatya',
    manisa: 'Manisa',
    mersin: 'Mersin',
    rize: 'Rize',
    samsun: 'Samsun',
    sanliurfa: 'Şanlıurfa',
    tekirdag: 'Tekirdağ',
    trabzon: 'Trabzon',
    van: 'Van',
    adana: 'Adana',
    ankara: 'Ankara',
    antalya: 'Antalya',
    bursa: 'Bursa',
    denizli: 'Denizli',
    hatay: 'Hatay',
    kayseri: 'Kayseri',
    izmir: 'İzmir',
    istanbul: 'İstanbul',
    gaziantep: 'Gaziantep',
    mugla: 'Muğla',
    sivas: 'Sivas',
    dugun: 'Düzce',
    duzce: 'Düzce',
    erzurum: 'Erzurum',
    ordu: 'Ordu',
    zonguldak: 'Zonguldak',
    canakkale: 'Çanakkale',
    edirne: 'Edirne',
    nigde: 'Niğde',
    karaman: 'Karaman',
    burdur: 'Burdur',
    bartin: 'Bartın',
    osmaniye: 'Osmaniye',
    mardin: 'Mardin',
    tokat: 'Tokat',
    kirklareli: 'Kırklareli',
    karabuk: 'Karabük',
  }
  return special[slug] ?? slug.charAt(0).toLocaleUpperCase('tr-TR') + slug.slice(1)
}

export default function OfflineCitiesCard(): ReactElement {
  const [downloaded, setDownloaded] = useState<OfflineCity[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [input, setInput] = useState('')

  useEffect(() => {
    listOfflineCities().then(setDownloaded).catch(() => setDownloaded([]))
  }, [])

  async function download(slug: string) {
    setBusy(slug)
    setError(null)

    let data: Awaited<ReturnType<typeof fetchTransitDataCity>> | null = null
    let lastMsg = ''

    // Mobil baglantida buyuk indirme bazen yarida kesilir; bir kez otomatik dene
    for (let attempt = 0; attempt < 2 && !data; attempt++) {
      if (attempt > 0) await new Promise((r) => setTimeout(r, 1500))
      try {
        data = await fetchTransitDataCity(displayName(slug))
      } catch (err) {
        lastMsg = err instanceof Error ? err.message : ''
      }
    }

    if (!data) {
      setError(`${displayName(slug)} indirilemedi. ${lastMsg || 'İnternet bağlantısını kontrol et.'}`)
      setBusy(null)
      return
    }

    try {
      await saveOfflineCity(data.city, data.stops)
      setDownloaded(await listOfflineCities())
    } catch {
      setError(`${displayName(slug)} indirildi ama telefona kaydedilemedi. Telefonda biraz yer açıp tekrar dene.`)
    } finally {
      setBusy(null)
    }
  }

  async function remove(slug: string) {
    setBusy(slug)
    try {
      await removeOfflineCity(slug)
      setDownloaded(await listOfflineCities())
    } finally {
      setBusy(null)
    }
  }

  const available = [
    'adana', 'afyon', 'ankara', 'antalya', 'balikesir', 'bursa', 'denizli',
    'diyarbakir', 'hatay', 'isparta', 'kahramanmaras', 'karaman', 'kastamonu',
    'kayseri', 'kocaeli', 'konya', 'malatya', 'manisa', 'mersin', 'nigde',
    'rize', 'samsun', 'sanliurfa', 'tekirdag', 'trabzon', 'van',
  ]
  const notDownloaded = available.filter(
    (c) => !downloaded.some((d) => d.city.toLowerCase() === c),
  )

  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">Çevrimdışı duraklar</p>
      <p className="mt-1 text-xs text-muted">
        Şehrin durak ve hatlarını telefona indir; internetsiz kaldığında bile
        en yakın duraklar ve hat bilgisi çalışır.
      </p>

      {downloaded.length > 0 && (
        <div className="mt-3 space-y-2">
          {downloaded.map((d) => (
            <div key={d.city} className="flex items-center justify-between rounded-xl border border-line/60 bg-bg/40 px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-bold">{displayName(d.city) || d.city}</p>
                <p className="text-[11px] text-muted">{d.stopCount} durak</p>
              </div>
              <button
                type="button"
                disabled={busy === d.city}
                onClick={() => remove(d.city)}
                className="shrink-0 rounded-lg border border-line px-2.5 py-1.5 text-[11px] font-bold text-muted transition-colors hover:border-red-400/50 hover:text-red-300"
              >
                Sil
              </button>
            </div>
          ))}
        </div>
      )}

      {notDownloaded.length > 0 && (
        <div className="mt-3">
          <select
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              if (e.target.value) void download(e.target.value)
            }}
            disabled={busy !== null}
            className="w-full rounded-xl border border-line bg-bg/60 px-3 py-2.5 text-sm font-bold outline-none focus:border-accent/60"
          >
            <option value="">{busy ? `${displayName(busy)} indiriliyor…` : 'Şehir indir +'}</option>
            {notDownloaded.map((c) => (
              <option key={c} value={c}>{displayName(c)}</option>
            ))}
          </select>
        </div>
      )}

      {error && <p role="alert" className="mt-2 text-xs text-red-300">{error}</p>}
    </div>
  )
}
