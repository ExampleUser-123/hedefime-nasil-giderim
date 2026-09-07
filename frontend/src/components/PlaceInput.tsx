import { useEffect, useRef, useState } from 'react'
import { fetchSuggestions, type PlaceSuggestion } from '@/lib/api'
import { getPinnedPlace, getLastCoords, saveLastCoords, type PinnedPlace } from '@/lib/storage'
import { IconPin } from '@/icons'

/**
 * Yer girişi: yazarken altında Google-benzeri öneri listesi düşer.
 * - value: aramada kullanılacak tam metin (display_name)
 * - onChange: seçim yapılınca veya yazınca çağrılır
 * Öneri seçilince input'a kısa isim yazılır, onChange'a tam isim gider.
 * Sabitlenmiş Ev/İş konumları öneri listesinin tepesinde çıkar.
 */
export default function PlaceInput({
  value,
  onChange,
  onPicked,
  placeholder,
  accent,
  endSlot,
  onSubmit,
}: {
  value: string
  onChange: (next: string) => void
  onPicked?: (coords: { lat: number; lon: number }) => void
  placeholder: string
  accent?: boolean
  endSlot?: React.ReactNode
  onSubmit?: () => void
}) {
  const [text, setText] = useState(value)
  const [items, setItems] = useState<PlaceSuggestion[]>([])
  const [open, setOpen] = useState(false)
  const boxRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null)
  const lastSyncedRef = useRef(value)
  const locationTriedRef = useRef(false)

  // Dis degisiklik (preset, swap, konum) -> metni esitle
  useEffect(() => {
    if (value !== lastSyncedRef.current) {
      lastSyncedRef.current = value
      setText(value)
    }
  }, [value])

  // Odak dýsý tiklamayi yakala
  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      if (!boxRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [])

  function handleChange(next: string) {
    setText(next)
    setOpen(true)
    lastSyncedRef.current = next
    onChange(next)

    // Konum izni onceden verildiyse sessizce koordinat kaydet; bir
    // kez denenir, basarisizsa kullaniciya dokunulmaz.
    if (!locationTriedRef.current) {
      locationTriedRef.current = true

      if (!getLastCoords() && 'geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (position) =>
            saveLastCoords(position.coords.latitude, position.coords.longitude),
          () => {},
          { enableHighAccuracy: false, timeout: 4000, maximumAge: 300000 },
        )
      }
    }

    if (debounceRef.current) clearTimeout(debounceRef.current)

    const trimmed = next.trim()

    if (trimmed.length < 3) {
      setItems([])
      return
    }

    debounceRef.current = setTimeout(() => {
      // Kayitli cihaz konumu varsa onerileri o bolgeye bicimlendir
      // ("fatih mahallesi" -> kullaniciya en yakin Fatih Mahallesi)
      fetchSuggestions(trimmed, getLastCoords() ?? undefined)
        .then((suggestions) => {
          setItems(suggestions)
        })
        .catch(() => {
          setItems([]) // öneri servisi kritik degil
        })
    }, 250)
  }

  function pick(suggestion: PlaceSuggestion) {
    setText(suggestion.name)
    lastSyncedRef.current = suggestion.display_name
    onChange(suggestion.display_name)
    setItems([])
    setOpen(false)
    onPicked?.({ lat: suggestion.lat, lon: suggestion.lon })
  }

  function pickPinned(place: PinnedPlace) {
    setText(place.label)
    lastSyncedRef.current = place.address
    onChange(place.address)
    setItems([])
    setOpen(false)
    onPicked?.({ lat: place.lat, lon: place.lon })
  }

  // Ev/Is sabit konumlari: odaaktayken onerilerin ustunde cikar
  const home = getPinnedPlace('home')
  const work = getPinnedPlace('work')
  const showPinned = open && text.trim().length === 0
  const showItems = open && items.length > 0 && text.trim().length >= 3

  return (
    <div ref={boxRef} className="relative">
      <div
        className={`flex items-center gap-3 rounded-xl bg-bg/60 px-4 py-3 transition-colors ${
          showItems ? 'rounded-b-none' : ''
        }`}
      >
        <IconPin className={`h-5 w-5 shrink-0 ${accent ? 'text-accent' : 'text-fg'}`} />
        <input
          value={text}
          onChange={(e) => handleChange(e.target.value)}
          onFocus={() => setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              setOpen(false)
              onSubmit?.()
            }
            if (e.key === 'Escape') setOpen(false)
          }}
          placeholder={placeholder}
          autoComplete="off"
          className="w-full bg-transparent text-[17px] font-medium outline-none"
        />
        {endSlot}
      </div>

      {showPinned && (home || work) && (
        <ul
          aria-label="Sabit konumlar"
          className="absolute inset-x-0 top-full z-[60] overflow-hidden rounded-b-xl border border-t-0 border-line bg-surface shadow-lg shadow-black/30"
        >
          {home && (
            <li>
              <button
                type="button"
                onClick={() => pickPinned(home)}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-bg/60 active:bg-bg"
              >
                <span aria-hidden="true">🏠</span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold">Ev</span>
                  <span className="block truncate text-xs text-muted">{home.address}</span>
                </span>
              </button>
            </li>
          )}
          {work && (
            <li>
              <button
                type="button"
                onClick={() => pickPinned(work)}
                className="flex w-full items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-bg/60 active:bg-bg"
              >
                <span aria-hidden="true">💼</span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold">İş</span>
                  <span className="block truncate text-xs text-muted">{work.address}</span>
                </span>
              </button>
            </li>
          )}
        </ul>
      )}

      {showItems && (
        <ul
          role="listbox"
          aria-label={placeholder}
          className="absolute inset-x-0 top-full z-[60] max-h-[21rem] overflow-y-auto overscroll-contain rounded-b-xl border border-t-0 border-line bg-surface shadow-lg shadow-black/30"
        >
          {items.map((item, index) => (
            <li key={`${item.lat}-${item.lon}-${index}`} role="option" aria-selected="false">
              <button
                type="button"
                onClick={() => pick(item)}
                className="flex w-full items-start gap-2 px-4 py-2.5 text-left transition-colors hover:bg-bg/60 active:bg-bg"
              >
                <IconPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted" />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-bold">{item.name}</span>
                  {item.detail && (
                    <span className="block truncate text-xs text-muted">{item.detail}</span>
                  )}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
