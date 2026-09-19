import {
  CATCH_BUFFER_MIN, clockAfter, computedAtMs, firstCatchable,
  isCatchable, liveMinutesAhead,
} from './departureTime.ts'

let pass = 0, fail = 0
function check(name, cond, extra = '') {
  if (cond) { pass++; console.log('PASS ' + name + (extra ? ' [' + extra + ']' : '')) }
  else { fail++; console.log('FAIL ' + name + (extra ? ' [' + extra + ']' : '')) }
}

// Sabit "simdi": 14:37 Istanbul = 11:37Z (Kis, +03)
const NOW = Date.parse('2026-01-15T11:37:00Z')
const iso = (minAhead) => new Date(NOW - 0).toISOString() // placeholder
const at = (wallHHMM) => {
  // ayni gunun duvar saatini computed_at yap (Istanbul = UTC+3, DST yok)
  const [h, m] = wallHHMM.split(':').map(Number)
  return new Date(Date.UTC(2026, 0, 15, h - 3, m, 0)).toISOString()
}
const dep = (time, ahead, src = 'gtfs') => ({ time, source: src, minutes_ahead: ahead, computed_at: at('14:37') })

// S1: 14:37 + liste [14:20(gecmis), 14:50, 15:20] -> canli degerler
check('S1. 14:50 -> 13 dk', liveMinutesAhead(dep('14:50', 13), NOW) === 13)
check('S1b. gecmis sefer negatif', liveMinutesAhead(dep('14:20', -17), NOW) === -17)

// S2: 14:47 + 8 dk yurume + 2 pay -> 14:50 (3 dk) yakalanamaz
const NOW2 = Date.parse('2026-01-15T11:47:00Z')
const d250 = { time: '14:50', source: 'gtfs', minutes_ahead: 3, computed_at: at('14:47') }
check('S2. 14:50 yakalanamaz', isCatchable(d250, 8, CATCH_BUFFER_MIN, NOW2) === false)
// ayni kosulda 15:10 (23 dk) yakalanir
const d310 = { time: '15:10', source: 'gtfs', minutes_ahead: 23, computed_at: at('14:47') }
check('S2b. 15:10 yakalanir', isCatchable(d310, 8, CATCH_BUFFER_MIN, NOW2) === true)
check('S2c. firstCatchable 15:10 secer',
  firstCatchable([d250, d310], 8, CATCH_BUFFER_MIN, NOW2)?.time === '15:10')

// S3: 23:58 + 8 dk yurume -> varis 00:06 (gece yarisi gecisi)
const NOW3 = Date.parse('2026-01-15T20:58:00Z') // 23:58+03
check('S3. 23:58+8dk = 00:06', clockAfter(NOW3, 8) === '00:06', clockAfter(NOW3, 8))
// 00:10 otobusu: 23:58'den 12 dk sonra
check('S3b. 00:10 icin kalan ~12 dk', clockAfter(NOW3, 12) === '00:10')

// S4: cihaz saati UTC de olsa Istanbul duvari gosterilir
check('S4. 14:37 duvari', clockAfter(NOW, 0) === '14:37', clockAfter(NOW, 0))

// tick: 5 dk sonra 14:50 -> 8 dk kalir
check('tick. 5 dk gecince azalir',
  liveMinutesAhead(dep('14:50', 13), NOW + 5 * 60000) === 8)

// computed_at yoksa taze sayilir
check('computed_at yoksa taze', liveMinutesAhead({ time: 'x', source: 'gtfs', minutes_ahead: 5 }, NOW) === 5)
check('bozuk computed_at taze sayilir',
  computedAtMs({ time: 'x', source: 'gtfs', minutes_ahead: 5, computed_at: 'bozuk' }, NOW) === NOW)

console.log(`\n${pass}/${pass + fail} gecti`)
process.exit(fail ? 1 : 0)
