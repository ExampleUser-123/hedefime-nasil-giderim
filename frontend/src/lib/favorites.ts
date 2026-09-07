import {
  addFavorite,
  deleteFavorite,
  fetchFavorites,
  getAuthToken,
  type ServerFavorite,
} from './api'
import { getSaved, type SavedRoute } from './storage'

export type FavoriteView = {
  id: string | null
  from: string
  to: string
  people: number
  mode: string
}

function toView(item: ServerFavorite): FavoriteView {
  return {
    id: item.id,
    from: item.from,
    to: item.to,
    people: item.people,
    mode: item.mode,
  }
}

function localToView(item: SavedRoute): FavoriteView {
  return {
    id: null,
    from: item.from,
    to: item.to,
    people: item.people,
    mode: item.mode,
  }
}

/**
 * Favorileri getirir: giris yapildiysa sunucudan, giris yapilmadiysa
 * yerel listeden (salt okunur; kaydetmek icin giris gerekir).
 */
export async function loadFavorites(): Promise<{ items: FavoriteView[]; serverBacked: boolean }> {
  if (!getAuthToken()) {
    return { items: getSaved().map(localToView), serverBacked: false }
  }

  const { favorites } = await fetchFavorites()

  return { items: favorites.map(toView), serverBacked: true }
}

export type ToggleResult = {
  saved: boolean
  needsLogin: boolean
  items?: FavoriteView[]
}

/**
 * Favori ekler/cikarir. Giris yapilmamissa needsLogin=true doner;
 * arayuz giris akisini acar.
 */
export async function toggleFavorite(
  entry: Omit<FavoriteView, 'id'>,
): Promise<ToggleResult> {
  if (!getAuthToken()) {
    return { saved: false, needsLogin: true }
  }

  const { favorites } = await fetchFavorites()
  const existing = favorites.find(
    (item) => item.from === entry.from && item.to === entry.to,
  )

  if (existing) {
    const { favorites: rest } = await deleteFavorite(existing.id)
    return { saved: false, needsLogin: false, items: rest.map(toView) }
  }

  const { favorites: next } = await addFavorite(entry)
  return { saved: true, needsLogin: false, items: next.map(toView) }
}

/**
 * Giris yapildiginda telefonda sakli eski favorileri hesaba tasir.
 * Donus: tasinan kayit sayisi.
 */
export async function migrateLocalFavorites(): Promise<number> {
  const local = getSaved()

  if (local.length === 0) return 0

  let migrated = 0

  for (const item of local) {
    try {
      await addFavorite({
        from: item.from,
        to: item.to,
        people: item.people,
        mode: item.mode,
      })
      migrated += 1
    } catch {
      // ayni guzergah zaten sunucudadaysa hata dusmez; digerlerine devam
    }
  }

  return migrated
}
