/* Hedefime Nasil Giderim - basit cevrimdisi/hizli-acilis Service Worker.
 * Strateji: ayni-kaynaktan GET isteklerinde Cache First, arka planda
 * tazele (stale-while-revalidate). Sayfa gecislerinde ag yoksa
 * index.html'e dus (offline fallback). Surum degisince eski onbellek silinir.
 */
const CACHE = 'hng-pwa-v1';

const CORE = [
  './',
  './index.html',
  './icon-192.png',
  './icon-512.png',
  './manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(CORE))
      .then(() => self.skipWaiting())
      .catch(() => {}),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim())
      .catch(() => {}),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(req, { ignoreSearch: false }).then((hit) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((cache) => cache.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(() => {
          // Ag yoksa: sayfa istegi ise ana sayfaya dus
          if (req.mode === 'navigate') {
            return caches.match('./index.html');
          }
          return hit || Response.error();
        });
      // Onbellek varsa aninda goster, yoksa agi bekle
      return hit || network;
    }),
  );
});
