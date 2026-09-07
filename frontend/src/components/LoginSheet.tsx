import { useState } from 'react'
import { signInWithGoogle } from '@/lib/auth'
import { migrateLocalFavorites } from '@/lib/favorites'
import { IconClose, IconLogo } from '@/icons'

export default function LoginSheet({
  open,
  onClose,
  onLoggedIn,
}: {
  open: boolean
  onClose: () => void
  onLoggedIn: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  async function handleSignIn() {
    if (busy) return

    setError(null)
    setBusy(true)

    try {
      await signInWithGoogle()
      await migrateLocalFavorites()
      onLoggedIn()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Giriş yapılamadı.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label="Giriş yap">
      <div className="absolute inset-0 bg-bg/70 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative w-full overflow-hidden rounded-t-3xl border border-line bg-surface p-6 sm:max-w-sm sm:rounded-3xl">
        <button
          type="button"
          onClick={onClose}
          aria-label="Kapat"
          className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-full text-muted transition-colors hover:bg-surface-2 hover:text-fg"
        >
          <IconClose className="h-5 w-5" />
        </button>

        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/15 text-accent">
          <IconLogo className="h-6 w-6" />
        </span>

        <h2 className="mt-3 text-lg font-bold">Google ile giriş yap</h2>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          Favori rotaların hesabına kaydedilsin, telefonda kalsın. AI asistanı da
          hesaplı kullanım için giriş istiyor.
        </p>

        <button
          type="button"
          onClick={handleSignIn}
          disabled={busy}
          className="mt-5 flex min-h-[48px] w-full items-center justify-center gap-3 rounded-2xl border border-line bg-surface-2 font-bold transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
            <path
              fill="#EA4335"
              d="M12 5.04c1.62 0 3.06.56 4.2 1.64l3.12-3.12C17.46 1.8 14.96.75 12 .75 7.4.75 3.44 3.4 1.53 7.26l3.66 2.84C6.1 7.31 8.8 5.04 12 5.04z"
            />
            <path
              fill="#4285F4"
              d="M23.25 12.26c0-.81-.07-1.59-.21-2.34H12v4.51h6.32c-.27 1.45-1.1 2.68-2.33 3.5l3.6 2.79c2.1-1.95 3.66-4.81 3.66-8.46z"
            />
            <path
              fill="#FBBC05"
              d="M5.19 14.4a7.2 7.2 0 0 1 0-4.3L1.53 7.26a11.26 11.26 0 0 0 0 9.98l3.66-2.84z"
            />
            <path
              fill="#34A853"
              d="M12 23.25c3.04 0 5.6-1 7.46-2.72l-3.6-2.79c-1 .68-2.3 1.08-3.86 1.08-3.2 0-5.9-2.27-6.81-5.32l-3.66 2.84c1.91 3.86 5.87 6.91 10.47 6.91z"
            />
          </svg>
          {busy ? 'Giriş yapılıyor…' : 'Google ile devam et'}
        </button>

        {error && (
          <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        <p className="mt-4 text-center text-xs text-muted">
          Şifren bende saklanmaz — giriş Google tarafından yapılır.
        </p>
      </div>
    </div>
  )
}
