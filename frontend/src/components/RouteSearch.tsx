import { useEffect, useRef, useState } from 'react'
import { fetchPlan, reverseGeocode, type Mode, type PlanResult, type Vehicle } from '@/lib/api'
import { addHistory, saveLastCoords } from '@/lib/storage'
import ResultsScreen from '@/components/ResultsScreen'
import VehiclePicker, { loadRememberedVehicle } from '@/components/VehiclePicker'
import type { VehicleType } from '@/lib/api'
import PlaceInput from '@/components/PlaceInput'
import {
  IconBus,
  IconCar,
  IconFerry,
  IconLocate,
  IconMetro,
  IconMoto,
  IconPlane,
  IconSparkle,
  IconSwap,
  IconTram,
  IconTrain,
  IconUsers,
  IconWalk,
} from '@/icons'

const MODES = [
  { id: 'tumu', label: 'Tümü', icon: IconSparkle },
  { id: 'otobus', label: 'Otobüs', icon: IconBus },
  { id: 'metro', label: 'Metro', icon: IconMetro },
  { id: 'tramvay', label: 'Tramvay', icon: IconTram },
  { id: 'motosiklet', label: 'Motosiklet', icon: IconMoto },
  { id: 'deniz', label: 'Deniz', icon: IconFerry },
  { id: 'tren', label: 'Tren', icon: IconTrain },
  { id: 'yuruyus', label: 'Yürüyüş', icon: IconWalk },
  { id: 'arac', label: 'Araba', icon: IconCar },
  { id: 'ucak', label: 'Uçak', icon: IconPlane },
] as const

export type SearchPreset = {
  from: string
  to: string
  people: number
  mode: Mode
  key: number
}

export default function RouteSearch({
  mode,
  onModeChange,
  plan,
  onPlanChange,
  preset,
  routeIndex,
  onRouteIndexChange,
  onRequireLogin,
}: {
  mode: Mode
  onModeChange: (mode: Mode) => void
  plan: PlanResult | null
  onPlanChange: (plan: PlanResult | null) => void
  preset: SearchPreset | null
  routeIndex: number
  onRouteIndexChange: (index: number) => void
  onRequireLogin: () => void
}) {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [loading, setLoading] = useState(false)
  const [locating, setLocating] = useState(false)
  const [people, setPeople] = useState(1)
  const [vehicle, setVehicle] = useState<Vehicle | null>(null)
  const [pickerOpen, setPickerOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const rememberedId = loadRememberedVehicle()

  function swap() {
    setFrom(to)
    setTo(from)
  }

  async function search(fromOverride?: string, toOverride?: string) {
    const start = (fromOverride ?? from).trim()
    const end = (toOverride ?? to).trim()

    if (!start || !end || loading) return

    setLoading(true)
    setError(null)

    try {
      const nextPlan = await fetchPlan(
        start,
        end,
        people,
        effectiveVehicleId,
      )
      onPlanChange(nextPlan)
      addHistory({ from: start, to: end, people, mode })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rota alınamadı.')
    } finally {
      setLoading(false)
    }
  }

  const lastPresetKey = useRef<number | null>(null)

  useEffect(() => {
    if (!preset || preset.key === lastPresetKey.current) return

    lastPresetKey.current = preset.key
    setFrom(preset.from)
    setTo(preset.to)
    setPeople(preset.people)

    if (preset.mode !== mode) onModeChange(preset.mode)

    search(preset.from, preset.to)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preset])

  function handleVehicleSelect(nextVehicle: Vehicle, remember: boolean) {
    setVehicle(nextVehicle)

    try {
      if (remember) {
        localStorage.setItem('hng-vehicle-id', nextVehicle.id)
        localStorage.setItem('hng-vehicle-name', nextVehicle.name)
        localStorage.setItem('hng-vehicle-type', nextVehicle.vehicle_type)
      } else {
        localStorage.removeItem('hng-vehicle-id')
        localStorage.removeItem('hng-vehicle-name')
        localStorage.removeItem('hng-vehicle-type')
      }
    } catch {
      // localStorage kapalıysa sessizce devam
    }

    setPickerOpen(false)
  }

  const rememberedName = (() => {
    try {
      return localStorage.getItem('hng-vehicle-name')
    } catch {
      return null
    }
  })()

  const rememberedType = (() => {
    try {
      return (localStorage.getItem('hng-vehicle-type') as VehicleType | null) ?? 'arac'
    } catch {
      return 'arac' as VehicleType
    }
  })()

  const selectedType: VehicleType = vehicle?.vehicle_type ?? rememberedType
  const RowVehicleIcon = selectedType === 'motosiklet' ? IconMoto : IconCar

  // Moda uygun araç: Motosiklet modunda motosiklet, Araba modunda araba kullanılır
  const isMotoMode = mode === 'motosiklet'
  const modeWantsType: VehicleType = isMotoMode ? 'motosiklet' : 'arac'
  const effectiveVehicleId = (() => {
    if (mode !== 'arac' && mode !== 'motosiklet') return vehicle?.id ?? rememberedId ?? undefined

    if (vehicle?.vehicle_type === modeWantsType) return vehicle.id
    if (!vehicle && rememberedId && rememberedType === modeWantsType) return rememberedId

    return isMotoMode ? 'honda_pcx' : 'toyota_corolla'
  })()

  const vehicleRowLabel =
    effectiveVehicleId === 'honda_pcx' && !vehicle && rememberedType !== 'motosiklet'
      ? 'Honda PCX 125 (varsayılan)'
      : effectiveVehicleId === 'toyota_corolla' && !vehicle && rememberedType !== 'arac'
        ? 'Toyota Corolla 1.6 (varsayılan)'
        : (vehicle?.name ?? rememberedName ?? '')

  function detectLocation() {
    if (locating) return

    if (!('geolocation' in navigator)) {
      setError('Tarayıcın konum desteği sunmuyor.')
      return
    }

    setLocating(true)
    setError(null)

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          saveLastCoords(position.coords.latitude, position.coords.longitude)

          const place = await reverseGeocode(
            position.coords.latitude,
            position.coords.longitude,
          )

          setFrom(place.display_name.split(',').slice(0, 2).join(','))
        } catch (e) {
          setError(
            e instanceof Error && e.message !== 'Sunucuya ulaşılamadı. Backend çalışıyor mu?'
              ? e.message
              : 'Konumun bulunamadı. Lütfen elle yaz.',
          )
        } finally {
          setLocating(false)
        }
      },
      () => {
        setLocating(false)
        setError('Konum izni alınamadı. Tarayıcı ayarlarından izin verip tekrar dene.')
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    )
  }

  return (
    <div>
      <div className="rounded-2xl border border-line bg-surface-2/90 p-4 backdrop-blur-sm">
        <div className="relative">
          <span className="absolute left-4 top-8 -bottom-8 w-px border-l border-dashed border-line" aria-hidden="true" />

          <PlaceInput
            value={from}
            onChange={setFrom}
            placeholder="Nereden"
            accent
            onSubmit={search}
            endSlot={
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  detectLocation()
                }}
                aria-label="Konumumu kullan"
                disabled={locating}
                className="absolute right-3 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-muted transition-colors hover:text-accent disabled:opacity-40"
              >
                {locating ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-muted/30 border-t-accent" aria-hidden="true" />
                ) : (
                  <IconLocate className="h-4.5 w-4.5" />
                )}
              </button>
            }
          />

          <div className="mt-3">
            <PlaceInput
              value={to}
              onChange={setTo}
              placeholder="Nereye"
              onSubmit={search}
            />
          </div>

          <button
            type="button"
            onClick={swap}
            aria-label="Başlangıç ve hedefi değiştir"
            className="absolute right-2 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-surface text-muted transition-colors hover:border-accent hover:text-accent"
          >
            <IconSwap className="h-4 w-4" />
          </button>
        </div>

        <div className="-mx-4 mt-4 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden" role="radiogroup" aria-label="Ulaşım türü">
          {MODES.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="radio"
              aria-checked={mode === id}
              onClick={() => onModeChange(id)}
              className={`flex min-h-[44px] shrink-0 items-center gap-1.5 rounded-full border px-4 text-sm font-medium transition-colors ${
                mode === id
                  ? 'border-accent bg-accent/10 text-accent'
                  : 'border-line bg-bg/40 text-muted hover:border-muted hover:text-fg'
              }`}
            >
              <Icon className="h-4.5 w-4.5" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {(mode === 'arac' || mode === 'motosiklet') && (
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            className="mt-3 flex w-full items-center justify-between rounded-xl bg-bg/60 px-3 py-2.5 text-left transition-colors hover:bg-bg"
          >
            <span className="flex items-center gap-2 text-sm text-muted">
              <RowVehicleIcon className="h-4 w-4" />
              <span className="truncate">
                {vehicleRowLabel || (isMotoMode ? 'Honda PCX 125 (varsayılan)' : 'Toyota Corolla 1.6 (varsayılan)')}
              </span>
            </span>
            <span className="shrink-0 text-xs font-bold text-accent">Değiştir</span>
          </button>
        )}
        <div className="mt-3 flex items-center justify-between rounded-xl bg-bg/60 px-3 py-2">
          <span className="flex min-w-20 items-center gap-2 text-sm font-bold tabular-nums" aria-live="polite">
            <IconUsers className="h-4 w-4 shrink-0 text-muted" />
            {people} kişi
          </span>
          <div className="flex items-center gap-1" role="group" aria-label="Kişi sayısı seçimi">
            <button
              type="button"
              onClick={() => setPeople((current) => Math.max(1, current - 1))}
              disabled={people <= 1}
              aria-label="Kişi sayısını azalt"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-lg font-bold text-muted transition-colors hover:bg-surface hover:text-accent disabled:opacity-30 disabled:hover:text-muted"
            >
              −
            </button>
            <button
              type="button"
              onClick={() => setPeople((current) => Math.min(8, current + 1))}
              disabled={people >= 8}
              aria-label="Kişi sayısını artır"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-lg font-bold text-muted transition-colors hover:bg-surface hover:text-accent disabled:opacity-30 disabled:hover:text-muted"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={() => search()}
        disabled={loading || !from.trim() || !to.trim()}
        className="mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-accent text-base font-bold text-accent-ink transition-transform hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-40"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent-ink/30 border-t-accent-ink" aria-hidden="true" />
            Rota aranıyor...
          </>
        ) : (
          'Rota Bul'
        )}
      </button>

      {error && (
        <p role="alert" className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {plan && (
        <ResultsScreen
          plan={plan}
          people={people}
          mode={mode}
          onBack={() => onPlanChange(null)}
          routeIndex={routeIndex}
          onRouteIndexChange={onRouteIndexChange}
          onRequireLogin={onRequireLogin}
        />
      )}

      <VehiclePicker
        open={pickerOpen}
        selectedId={vehicle?.id ?? rememberedId ?? ''}
        initialType={isMotoMode ? 'motosiklet' : 'arac'}
        onClose={() => setPickerOpen(false)}
        onSelect={handleVehicleSelect}
      />
    </div>
  )
}
