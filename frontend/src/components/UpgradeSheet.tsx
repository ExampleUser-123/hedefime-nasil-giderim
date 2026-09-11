import { useState } from 'react'
import type { Tier } from '@/lib/api'

type Plan = {
  id: Tier
  name: string
  price: string
  note?: string
  highlight?: boolean
  routes: string
  ai: string
  ads: string
  extras: string[]
}

const PLANS: Plan[] = [
  {
    id: 'free',
    name: 'Ücretsiz',
    price: '0 TL',
    routes: 'Günde 7 rota',
    ai: 'Günde 7 AI mesajı',
    ads: 'Her rota aramasında kısa reklam',
    extras: ['Tüm şehirler', 'Durak saatleri'],
  },
  {
    id: 'lite',
    name: 'Lite',
    price: '149 TL',
    note: 'İlk 1 ay özel fiyat',
    highlight: true,
    routes: 'Günde 20 rota',
    ai: 'Günde 30 AI mesajı',
    ads: 'Her 3 aramada bir reklam',
    extras: ['Tüm şehirler', 'Durak saatleri', 'Öncelikli destek'],
  },
  {
    id: 'premium',
    name: 'Premium',
    price: '250 TL',
    routes: 'Sınırsız rota',
    ai: 'Sınırsız AI sohbet',
    ads: 'Reklamsız deneyim',
    extras: ['Tüm şehirler', 'Durak saatleri', 'Öncelikli destek', 'Yeni özelliklere erken erişim'],
  },
]

/**
 * Uyelik planlari ekrani. Odeme altyapisi (Play Billing) entegre edilene
 * kadar satinalma butonu odeme yolunu gosterir.
 */
export default function UpgradeSheet({ onClose }: { onClose: () => void }) {
  const [selected, setSelected] = useState<Tier>('lite')

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-label="Üyelik planları"
        className="max-h-[88vh] w-full max-w-md overflow-y-auto rounded-t-3xl border border-white/10 bg-[#0f1524] p-5 pb-8"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-black text-white">Üyelik planları</h2>
            <p className="mt-1 text-sm text-muted">
              Daha çok rota, daha çok AI, reklamsız deneyim.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Kapat"
            className="rounded-full p-2 text-muted hover:bg-white/5"
          >
            ✕
          </button>
        </div>

        <div className="space-y-3">
          {PLANS.map((p) => {
            const active = selected === p.id
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => setSelected(p.id)}
                className={`w-full rounded-2xl border p-4 text-left transition ${
                  active
                    ? 'border-teal-400 bg-teal-400/10'
                    : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-extrabold text-white">{p.name}</span>
                    {p.highlight && (
                      <span className="rounded-full bg-teal-400/20 px-2 py-0.5 text-[10px] font-bold text-teal-300">
                        EN POPÜLER
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-black text-white">
                      {p.price}
                      <span className="text-xs font-normal text-muted">/ay</span>
                    </div>
                    {p.note && <div className="text-[10px] font-semibold text-teal-300">{p.note}</div>}
                  </div>
                </div>
                <ul className="mt-3 space-y-1 text-sm text-[#c7d2e5]">
                  <li>🧭 {p.routes}</li>
                  <li>✨ {p.ai}</li>
                  <li>🚫 {p.ads}</li>
                  {p.extras.slice(2).map((x) => (
                    <li key={x}>⭐ {x}</li>
                  ))}
                </ul>
              </button>
            )
          })}
        </div>

        <button
          type="button"
          disabled={selected === 'free'}
          onClick={() => {
            // Odeme altyapisi (Play Billing) entegre edilene kadar
            const contact = 'destek@hedefimenasilgiderim.com'
            window.location.href = `mailto:${contact}?subject=${encodeURIComponent(
              'Üyelik: ' + selected,
            )}`
          }}
          className={`mt-5 w-full rounded-2xl px-4 py-3.5 text-base font-black transition ${
            selected === 'free'
              ? 'cursor-not-allowed bg-white/5 text-muted'
              : 'bg-teal-400 text-slate-900 active:scale-[0.99]'
          }`}
        >
          {selected === 'free' ? 'Zaten ücretsiz planı kullanıyorsun' : `${PLANS.find((p) => p.id === selected)!.name} planına geç`}
        </button>
        <p className="mt-2 text-center text-xs text-muted">
          Ödemeler Play Store üzerinden güvenle alınır. Dilediğin zaman iptal edebilirsin.
        </p>
      </div>
    </div>
  )
}
