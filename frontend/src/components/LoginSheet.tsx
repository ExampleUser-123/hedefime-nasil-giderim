import { useState } from 'react'
import { signInWithEmail, signInWithGoogle, signUpWithEmail } from '@/lib/auth'
import { migrateLocalFavorites } from '@/lib/favorites'
import { IconClose, IconLogo } from '@/icons'

type Mode = 'google' | 'login' | 'register'

export default function LoginSheet({
  open,
  onClose,
  onLoggedIn,
}: {
  open: boolean
  onClose: () => void
  onLoggedIn: () => void
}) {
  const [mode, setMode] = useState<Mode>('google')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')

  if (!open) return null

  async function finish() {
    await migrateLocalFavorites()
    onLoggedIn()
    onClose()
  }

  async function handleSignIn() {
    if (busy) return

    setError(null)
    setBusy(true)

    try {
      await signInWithGoogle()
      await finish()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Giriş yapılamadı.')
    } finally {
      setBusy(false)
    }
  }

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (busy) return

    setError(null)

    const emailTrim = email.trim()
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(emailTrim)) {
      setError('Geçerli bir e-posta adresi gir.')
      return
    }
    if (password.length < 6) {
      setError('Şifre en az 6 karakter olmalı.')
      return
    }

    setBusy(true)

    try {
      if (mode === 'register') {
        await signUpWithEmail(emailTrim, password, name)
      } else {
        await signInWithEmail(emailTrim, password)
      }
      await finish()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'İşlem başarısız oldu.'

      // Register'da 409: hesap var -> girise yonlendir
      if (mode === 'register' && message.includes('zaten kayitli')) {
        setError('Bu e-posta zaten kayıtlı. Giriş yapmayı dene.')
        return
      }
      setError(message)
    } finally {
      setBusy(false)
    }
  }

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label="Giriş yap">
      <div className="absolute inset-0 bg-bg/70 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative max-h-[92dvh] w-full overflow-y-auto rounded-t-3xl border border-line bg-surface p-6 sm:max-w-sm sm:rounded-3xl">
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

        <h2 className="mt-3 text-lg font-bold">Hesabına giriş yap</h2>
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
          {busy && mode === 'google' ? 'Giriş yapılıyor…' : 'Google ile devam et'}
        </button>

        <div className="my-4 flex items-center gap-3" aria-hidden="true">
          <span className="h-px flex-1 bg-line" />
          <span className="text-xs text-muted">veya e-posta ile</span>
          <span className="h-px flex-1 bg-line" />
        </div>

        <div className="grid grid-cols-2 gap-1 rounded-xl bg-surface-2 p-1" role="tablist" aria-label="E-posta giriş türü">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            onClick={() => switchMode('login')}
            className={`min-h-[40px] rounded-lg text-sm font-bold transition-colors ${
              mode === 'login' ? 'bg-surface text-accent shadow-sm' : 'text-muted'
            }`}
          >
            Giriş yap
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'register'}
            onClick={() => switchMode('register')}
            className={`min-h-[40px] rounded-lg text-sm font-bold transition-colors ${
              mode === 'register' ? 'bg-surface text-accent shadow-sm' : 'text-muted'
            }`}
          >
            Kaydol
          </button>
        </div>

        {mode !== 'google' && (
          <form onSubmit={handleEmailSubmit} className="mt-4 space-y-3">
            {mode === 'register' && (
              <label className="block">
                <span className="mb-1 block text-xs font-bold text-muted">Adın (isteğe bağlı)</span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={40}
                  autoComplete="name"
                  placeholder="Örn. Ömer"
                  className="min-h-[46px] w-full rounded-xl border border-line bg-bg px-3 text-sm outline-none transition-colors focus:border-accent"
                />
              </label>
            )}

            <label className="block">
              <span className="mb-1 block text-xs font-bold text-muted">E-posta</span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                inputMode="email"
                placeholder="ornek@mail.com"
                className="min-h-[46px] w-full rounded-xl border border-line bg-bg px-3 text-sm outline-none transition-colors focus:border-accent"
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-xs font-bold text-muted">Şifre</span>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                placeholder="En az 6 karakter"
                className="min-h-[46px] w-full rounded-xl border border-line bg-bg px-3 text-sm outline-none transition-colors focus:border-accent"
              />
            </label>

            <button
              type="submit"
              disabled={busy}
              className="flex min-h-[48px] w-full items-center justify-center rounded-xl bg-accent font-bold text-accent-ink transition-transform hover:scale-[1.01] disabled:opacity-50"
            >
              {busy ? 'İşleniyor…' : mode === 'register' ? 'Hesap oluştur' : 'Giriş yap'}
            </button>
          </form>
        )}

        {error && (
          <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        <p className="mt-4 text-center text-xs text-muted">
          Şifren sunucuda şifrelenmiş olarak saklanır, kimse göremez.
        </p>
      </div>
    </div>
  )
}
