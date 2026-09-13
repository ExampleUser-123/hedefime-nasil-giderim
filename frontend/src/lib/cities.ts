// Desteklenen sehirler: durak verisi olan iller + yaygin takma adlar.
// Amaç: "Kadıköy, İstanbul, Marmara Bölgesi, Türkiye" gibi tam adresten
// gerçek şehri bulmak (son parça her zaman şehir değil — "Türkiye" tuzağı).

const KNOWN_CITIES = new Set([
  'adana', 'afyonkarahisar', 'afyon', 'ankara', 'antalya', 'alanya',
  'balikesir', 'bartin', 'bolu', 'bursa', 'burdur', 'canakkale', 'denizli',
  'diyarbakir', 'duzce', 'edirne', 'erzurum', 'eskisehir', 'gaziantep',
  'hatay', 'isparta', 'istanbul', 'izmir', 'izmit', 'kahramanmaras',
  'karabuk', 'karaman', 'kastamonu', 'kayseri', 'kirklareli', 'kocaeli',
  'konya', 'malatya', 'manisa', 'mardin', 'mersin', 'mugla', 'nigde',
  'ordu', 'osmaniye', 'rize', 'samsun', 'sanliurfa', 'sivas', 'tekirdag',
  'tokat', 'trabzon', 'van', 'zonguldak',
])

function normTr(s: string): string {
  return s
    .replace(/[çÇ]/g, 'c')
    .replace(/[ğĞ]/g, 'g')
    .replace(/[ıİ]/g, 'i')
    .replace(/[öÖ]/g, 'o')
    .replace(/[şŞ]/g, 's')
    .replace(/[üÜ]/g, 'u')
    .toLowerCase()
    .trim()
}

/** Tam adresten bilinen bir şehir adı çıkarır; bulamazsa son parçayı döner. */
export function extractCity(place: string): string {
  if (!place) return ''
  const parts = place.split(',').map((p) => p.trim()).filter(Boolean)
  for (const part of parts) {
    if (KNOWN_CITIES.has(normTr(part))) return part
  }
  return parts[parts.length - 1] ?? place
}
