import { useEffect, useMemo, useState } from 'react'
import { fetchVehicles, type Vehicle, type VehicleType } from '@/lib/api'
import { IconCar, IconClose, IconMoto } from '@/icons'

const STORAGE_KEY = 'hng-vehicle-id'

export function loadRememberedVehicle(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export default function VehiclePicker({
  open,
  selectedId,
  initialType = 'arac',
  onClose,
  onSelect,
}: {
  open: boolean
  selectedId: string
  initialType?: VehicleType
  onClose: () => void
  onSelect: (vehicle: Vehicle, remember: boolean) => void
}) {
  const [vehicles, setVehicles] = useState<Vehicle[] | null>(null)
  const [query, setQuery] = useState('')
  const [remember, setRemember] = useState(() => loadRememberedVehicle() !== null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open || vehicles) return

    fetchVehicles()
      .then(setVehicles)
      .catch((e) => setError(e instanceof Error ? e.message : 'Araç listesi alınamadı.'))
  }, [open, vehicles])

  const filtered = useMemo(() => {
    if (!vehicles) return []

    const q = query.trim().toLocaleLowerCase('tr')

    return vehicles.filter((v) => {
      // Eski backend cevaplarında vehicle_type yok; hepsi Otomobil sayılır
      const vType = v.vehicle_type ?? 'arac'

      if (vType !== initialType) return false

      if (!q) return true

      return (
        v.name.toLocaleLowerCase('tr').includes(q) ||
        v.brand.toLocaleLowerCase('tr').includes(q)
      )
    })
  }, [vehicles, query, initialType])

  if (!open) return null

  const PickerIcon = initialType === 'motosiklet' ? IconMoto : IconCar

  return (
    <div
      className="absolute inset-0 z-20 flex items-end justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label={initialType === 'motosiklet' ? 'Motosiklet seç' : 'Araç seç'}
      onClick={onClose}
    >
      <div
        className="max-h-[80%] w-full max-w-md overflow-hidden rounded-t-3xl border border-line bg-surface shadow-2xl sm:rounded-3xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <h2 className="flex items-center gap-2 text-sm font-bold">
            <PickerIcon className="h-4 w-4 text-accent" />
            {initialType === 'motosiklet' ? 'Motorunu seç' : 'Aracını seç'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Kapat"
            className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:bg-bg hover:text-fg"
          >
            <IconClose className="h-4 w-4" />
          </button>
        </div>

        <div className="border-b border-line px-4 py-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Marka veya model ara..."
            className="w-full rounded-xl bg-bg/60 px-3 py-2 text-sm outline-none ring-1 ring-line focus:ring-accent"
            autoFocus
          />
        </div>

        <label className="flex items-center gap-2.5 border-b border-line bg-accent/5 px-4 py-3 text-sm font-medium">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="h-4 w-4 accent-[var(--color-accent)]"
          />
          Bu aracı hatırla (her seferinde sorma)
        </label>

        <div className="max-h-[55vh] overflow-y-auto">
          {error && (
            <p className="px-4 py-4 text-sm text-red-300">{error}</p>
          )}

          {!error && vehicles === null && (
            <p className="px-4 py-4 text-sm text-muted">Araçlar yükleniyor...</p>
          )}

          {vehicles !== null && filtered.length === 0 && (
            <p className="px-4 py-4 text-sm text-muted">Sonuç bulunamadı.</p>
          )}

          <ul className="divide-y divide-line/60">
            {filtered.map((vehicle) => (
              <li key={vehicle.id}>
                <button
                  type="button"
                  onClick={() => onSelect(vehicle, remember)}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-surface-2/60 ${
                    vehicle.id === selectedId ? 'bg-accent/10' : ''
                  }`}
                >
                  <div>
                    <p className="text-sm font-medium">{vehicle.name}</p>
                    <p className="text-xs text-muted">
                      {vehicle.fuel_type} · {vehicle.consumption} L/100km
                    </p>
                  </div>
                  {vehicle.id === selectedId && (
                    <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-bold text-accent-ink">
                      Seçili
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
