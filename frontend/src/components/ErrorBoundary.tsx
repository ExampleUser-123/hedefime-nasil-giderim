import { Component, type ReactElement, type ReactNode } from 'react'

type Props = {
  children: ReactNode
}

type State = {
  hasError: boolean
}

/** Kuresel render hatasi yakalayici: beyaz ekran yerine kurtarma karti gosterir. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: unknown): void {
    try {
      // eslint-disable-next-line no-console
      console.error('[ErrorBoundary]', error)
    } catch {
      // log bile basarisizsa sessiz gec
    }
  }

  private retry = (): void => {
    this.setState({ hasError: false })
  }

  render(): ReactNode {
    if (!this.state.hasError) return this.props.children
    return (
      <div className="flex min-h-dvh items-center justify-center bg-bg p-6">
        <div className="w-full max-w-sm rounded-2xl border border-line bg-surface-2/90 p-6 text-center">
          <p className="text-3xl" aria-hidden>
            🛠️
          </p>
          <p className="mt-2 text-base font-bold text-fg">Bir şeyler ters gitti</p>
          <p className="mt-1 text-xs text-muted">
            Uygulama beklenmedik bir hatayla karşılaştı. Verileriniz kaybolmadı.
          </p>
          <button
            type="button"
            onClick={this.retry}
            className="mt-4 min-h-[44px] w-full rounded-xl bg-accent px-4 text-sm font-bold text-accent-ink"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    ) as ReactElement
  }
}
