import { useEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { createChatSession, sendAssistantMessage, type ChatMessage } from '@/lib/api'
import { IconClose, IconGlobe, IconSend, IconSparkle } from '@/icons'

const SESSION_KEY = 'hng-session-id'

export default function ChatDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages, open])

  async function ensureSession(): Promise<string> {
    const stored = localStorage.getItem(SESSION_KEY)

    if (stored) return stored

    const session = await createChatSession()
    localStorage.setItem(SESSION_KEY, session.id)

    return session.id
  }

  async function send() {
    const text = input.trim()

    if (!text || sending) return

    setInput('')
    setError(null)
    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', text }])

    try {
      const sessionId = await ensureSession()
      const reply = await sendAssistantMessage(sessionId, text)

      setMessages((prev) => [
        ...prev,
        { role: 'model', text: reply.reply, searchUsed: reply.search_used },
      ])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cevap alınamadı.')
    } finally {
      setSending(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true" aria-label="AI Asistan">
      <div className="absolute inset-0 bg-bg/70 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative flex h-[85vh] w-full flex-col overflow-hidden rounded-t-3xl border border-line bg-surface sm:h-[70vh] sm:max-w-lg sm:rounded-3xl">
        <header className="flex items-center gap-3 border-b border-line px-5 py-4">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-accent-ink">
            <IconSparkle className="h-4.5 w-4.5" />
          </span>
          <div>
            <p className="text-sm font-bold">AI Asistan</p>
            <p className="text-xs text-muted">Seyahat planlama asistanın</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Sohbeti kapat"
            className="ml-auto flex h-10 w-10 items-center justify-center rounded-full text-muted transition-colors hover:bg-surface-2 hover:text-fg"
          >
            <IconClose className="h-5 w-5" />
          </button>
        </header>

        <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
          {messages.length === 0 && !error && (
            <div className="mt-6 rounded-2xl border border-line bg-surface-2 p-4 text-sm leading-relaxed text-muted">
              Merhaba! Bana nereye gitmek istediğini yaz, rota, maliyet ve hava durumu bilgisiyle
              senin için en uygun yolu bulayım. Örneğin: <span className="text-fg">"Yarın Kadıköy'den İzmir'e iki kişi gideceğim, en ucuz yol hangisi?"</span>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  message.role === 'user'
                    ? 'rounded-br-md bg-accent text-accent-ink'
                    : 'rounded-bl-md border border-line bg-surface-2 text-fg'
                }`}
              >
                <Markdown
                  components={{
                    p: ({ children }) => <p className="my-1.5 first:mt-0 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="my-1.5 list-disc space-y-1 pl-4 first:mt-0 last:mb-0">{children}</ul>,
                    ol: ({ children }) => <ol className="my-1.5 list-decimal space-y-1 pl-4 first:mt-0 last:mb-0">{children}</ol>,
                    li: ({ children }) => <li className="pl-0.5">{children}</li>,
                    strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                    a: ({ children, href }) => (
                      <a href={href} target="_blank" rel="noreferrer" className="underline underline-offset-2">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {message.text}
                </Markdown>

                {message.searchUsed && (
                  <p className={`mt-2 flex items-center gap-1.5 text-xs ${message.role === 'user' ? 'text-accent-ink/70' : 'text-muted'}`}>
                    <IconGlobe className="h-3.5 w-3.5" />
                    İnternetten araştırıldı
                  </p>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div className="flex justify-start">
              <div className="flex gap-1.5 rounded-2xl rounded-bl-md border border-line bg-surface-2 px-4 py-3.5">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted [animation-delay:0ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted [animation-delay:150ms]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted [animation-delay:300ms]" />
              </div>
            </div>
          )}

          {error && (
            <p role="alert" className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </p>
          )}
        </div>

        <footer className="border-t border-line p-4">
          <div className="flex items-center gap-2 rounded-2xl border border-line bg-surface-2 px-4 py-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
              placeholder="Bir mesaj yaz..."
              className="min-h-[44px] w-full bg-transparent text-[15px] outline-none"
            />
            <button
              type="button"
              onClick={send}
              disabled={!input.trim() || sending}
              aria-label="Gönder"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-ink transition-opacity disabled:opacity-40"
            >
              <IconSend className="h-4.5 w-4.5" />
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}
