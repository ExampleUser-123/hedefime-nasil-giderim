import { Capacitor } from '@capacitor/core'
import { LocalNotifications } from '@capacitor/local-notifications'

export type DepartureReminder = {
  id: number
  stopName: string
  city: string
  line: string
  time: string // 'HH:MM'
  leadMin: number
}

const STORAGE_KEY = 'sefer_hatirlaticlari_v1'

// 'HH:MM' -> bugunun tarihi uzerinde Date; gectiyse yarinki gun.
export function nextOccurrence(time: string): Date {
  const [h, m] = time.split(':').map((x) => Number.parseInt(x, 10))
  const now = new Date()
  const at = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0, 0)

  if (at.getTime() <= now.getTime()) {
    at.setDate(at.getDate() + 1)
  }
  return at
}

// Adi kararli (ayni sefer -> ayni id): FNV-1a, 31 bite sigdirilir.
function reminderId(stopName: string, city: string, line: string, time: string): number {
  const str = `${city}|${stopName}|${line}|${time}`
  let hash = 0x811c9dc5

  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193)
  }
  return hash & 0x7fffffff
}

function readStore(): DepartureReminder[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as DepartureReminder[]) : []
  } catch {
    return []
  }
}

function writeStore(list: DepartureReminder[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

export function listReminders(): DepartureReminder[] {
  return readStore()
}

export function isReminderActive(stopName: string, city: string, line: string, time: string): boolean {
  const id = reminderId(stopName, city, line, time)
  return readStore().some((r) => r.id === id)
}

async function ensureChannel(): Promise<void> {
  if (!Capacitor.isNativePlatform()) return

  await LocalNotifications.createChannel({
    id: 'seferler',
    name: 'Sefer hatırlatıcıları',
    importance: 5, // HIGH
    visibility: 1, // PUBLIC
    sound: 'notification.wav',
  }).catch(() => {})
}

async function ensurePermission(): Promise<boolean> {
  if (!Capacitor.isNativePlatform()) return true

  const cur = await LocalNotifications.checkPermissions()
  if (cur.display === 'granted') return true

  const req = await LocalNotifications.requestPermissions()
  return req.display === 'granted'
}

async function scheduleOne(reminder: DepartureReminder, notifyAt: Date): Promise<void> {
  await ensureChannel()
  await LocalNotifications.schedule({
    notifications: [
      {
        id: reminder.id,
        title: `${reminder.line} hattı yaklaşıyor`,
        body: `${reminder.time} seferi için ${reminder.leadMin} dk kaldı — ${reminder.stopName} (${reminder.city})`,
        schedule: { at: notifyAt, allowWhileIdle: true },
        channelId: 'seferler',
      },
    ],
  })
}

export type AddReminderResult =
  | { ok: true }
  | { ok: false; reason: 'permission' | 'too-late' | 'failed' }

/**
 * Bir sefer icin hatirlatic kurar (sefer saati - leadMin).
 * Sadece bir sonraki olusum icin planlanir; uygulama acilinca rescheduleAll
 * gecenleri temizler.
 */
export async function addReminder(opts: {
  stopName: string
  city: string
  line: string
  time: string
  leadMin: number
}): Promise<AddReminderResult> {
  try {
    const ok = await ensurePermission()
    if (!ok) return { ok: false, reason: 'permission' }

    const notifyAt = new Date(nextOccurrence(opts.time).getTime() - opts.leadMin * 60_000)

    // Uyari zamani simdiden onceye dusmusse (sefer cok yakin) planlanamaz
    if (notifyAt.getTime() <= Date.now() + 30_000) {
      return { ok: false, reason: 'too-late' }
    }

    const reminder: DepartureReminder = {
      id: reminderId(opts.stopName, opts.city, opts.line, opts.time),
      stopName: opts.stopName,
      city: opts.city,
      line: opts.line,
      time: opts.time,
      leadMin: opts.leadMin,
    }

    await scheduleOne(reminder, notifyAt)

    const list = readStore().filter((r) => r.id !== reminder.id)
    list.push(reminder)
    writeStore(list)

    return { ok: true }
  } catch {
    return { ok: false, reason: 'failed' }
  }
}

export async function cancelReminder(stopName: string, city: string, line: string, time: string): Promise<void> {
  const id = reminderId(stopName, city, line, time)

  try {
    await LocalNotifications.cancel({ notifications: [{ id }] })
  } catch {
    // iptal basarisiz olsa da kaydi dusur
  }
  writeStore(readStore().filter((r) => r.id !== id))
}

/**
 * Uygulama acilirken: gecmis hatirlaticlari temizler, hala gelecekte olanlarin
 * bildirimi sistemde kayitli degilse yeniden planlar (one-shot + yeniden kurulum).
 */
export async function rescheduleAll(): Promise<void> {
  const list = readStore()
  if (list.length === 0) return

  let pendingIds: Set<number> | null = null

  try {
    const pending = await LocalNotifications.getPending()
    pendingIds = new Set(pending.notifications.map((n) => n.id))
  } catch {
    pendingIds = null
  }

  const nextList: DepartureReminder[] = []

  for (const r of list) {
    const notifyAt = new Date(nextOccurrence(r.time).getTime() - r.leadMin * 60_000)

    if (notifyAt.getTime() <= Date.now() + 30_000) continue // gecti, dusur

    if (pendingIds === null || pendingIds.has(r.id)) {
      nextList.push(r)
      continue // sistemde hala kayitli
    }

    try {
      await scheduleOne(r, notifyAt)
      nextList.push(r)
    } catch {
      // planlanamadiysa sessizce dusur
    }
  }

  writeStore(nextList)
}
