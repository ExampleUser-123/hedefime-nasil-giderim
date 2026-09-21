import { useEffect, useState, type ReactElement } from 'react'
import { fetchGameProfile, fetchInviteCode, fetchMagicUsage, type GameProfile } from '@/lib/api'
import { getStoredUser } from '@/lib/auth'

/** Profil ici gamification ozeti: XP, seviye, rozetler, Magic hakki. */
export default function GameSection(): ReactElement {
  const [profile, setProfile] = useState<GameProfile | null>(null)
  const [magic, setMagic] = useState<{ used: number; limit: number } | null>(null)
  const [invite, setInvite] = useState<string | null>(null)
  const [inviteMsg, setInviteMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!getStoredUser()) return
    let alive = true
    fetchGameProfile()
      .then((p) => {
        if (alive) setProfile(p)
      })
      .catch(() => {})
    fetchMagicUsage()
      .then((u) => {
        if (alive) setMagic({ used: u.used, limit: u.limit })
      })
      .catch(() => {})
    fetchInviteCode()
      .then((d) => {
        if (alive && d.code) setInvite(d.code)
      })
      .catch(() => {})
    return () => {
      alive = false
    }
  }, [])

  async function shareInvite() {
    if (!invite) return
    const url = `${window.location.origin}${window.location.pathname}?ref=${invite}`
    const text = `Hedefime Nasıl Giderim'e katıl, birlikte gezelim! Davet kodum: ${invite}`
    try {
      const nav = navigator as Navigator & { share?: (d: { title: string; text: string; url: string }) => Promise<void> }
      if (typeof nav.share === 'function') {
        await nav.share({ title: 'Hedefime Nasıl Giderim', text, url })
        setInviteMsg('Paylaşıldı! Arkadaşın kayıt olursa +50 XP kazanırsın.')
        return
      }
      throw new Error('paylasim yok')
    } catch {
      try {
        await navigator.clipboard.writeText(`${text} ${url}`)
        setInviteMsg('Davet linki panoya kopyalandı! Arkadaşın kayıt olursa +50 XP.')
      } catch {
        setInviteMsg(`Davet kodun: ${invite}`)
      }
    }
  }

  if (!getStoredUser()) return <></>

  return (
    <div className="mt-3 rounded-2xl border border-line bg-surface-2/90 p-4">
      <p className="text-xs uppercase tracking-wide text-muted">Rozetler ve Seviye</p>

      {profile ? (
        <>
          <div className="mt-2 flex items-center justify-between">
            <p className="text-sm font-bold">Seviye {profile.level}</p>
            <p className="text-xs text-muted tabular-nums">{profile.xp} XP</p>
          </div>
          <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-bg">
            <div
              className="h-full rounded-full bg-accent transition-all"
              style={{ width: `${profile.progress}%` }}
            />
          </div>

          {profile.badges.length > 0 ? (
            <div className="mt-3 grid grid-cols-3 gap-2">
              {profile.badges.map((b) => (
                <div
                  key={b.id}
                  title={b.desc}
                  className="rounded-xl border border-line/60 bg-bg/40 p-2 text-center"
                >
                  <span className="text-2xl" aria-hidden="true">{b.icon}</span>
                  <p className="mt-0.5 text-[11px] font-bold leading-tight">{b.name}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-xs text-muted">
              Henüz rozet yok — rota oluştur, yürü, toplu taşıma kullan, hedef ekle.
            </p>
          )}
        </>
      ) : (
        <p className="mt-2 text-xs text-muted">Yükleniyor…</p>
      )}

      {magic && (
        <p className="mt-3 border-t border-line/60 pt-2 text-xs text-muted">
          📍 Magic Share hakkı: {magic.limit < 0 ? 'sınırsız' : `${Math.max(0, magic.limit - magic.used)}/${magic.limit} kaldı`}
        </p>
      )}

      {invite && (
        <div className="mt-2">
          <button
            type="button"
            onClick={() => void shareInvite()}
            className="w-full rounded-xl border border-accent/40 py-2 text-xs font-bold text-accent"
          >
            🎁 Arkadaşınla Paylaş / Davet Et (+50 XP)
          </button>
          {inviteMsg && (
            <p role="status" className="mt-2 text-[11px] text-muted">{inviteMsg}</p>
          )}
        </div>
      )}
    </div>
  )
}
