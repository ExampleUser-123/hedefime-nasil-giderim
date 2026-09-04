import { IconChevronRight, IconSparkle } from '@/icons'

export default function AiBanner({ onOpen }: { onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group flex w-full items-center gap-3.5 rounded-2xl border border-accent/40 bg-gradient-to-r from-accent/15 to-accent/5 p-4 text-left transition-colors hover:border-accent"
    >
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-ink">
        <IconSparkle className="h-5 w-5" />
      </span>

      <span className="min-w-0 flex-1">
        <span className="block text-sm font-bold">AI Asistan</span>
        <span className="mt-0.5 block truncate text-sm text-muted">
          Bugün nereye gitmek istersin? Sana en iyi rotayı bulayım.
        </span>
      </span>

      <IconChevronRight className="h-5 w-5 shrink-0 text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-accent" />
    </button>
  )
}
