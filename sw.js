const CACHE_NAME = 'fare-share-v9';

// App shell (stesso dominio) + librerie esterne che non cambiano spesso:
// cacheate cache-first così l'app e la mappa restano utilizzabili offline
// dopo la prima visita. I marker di default di Leaflet sono inclusi perché
// altrimenti verrebbero richiesti al volo al primo utilizzo della mappa.
const APP_SHELL = [
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
];

// Host di servizi che devono restare "network-first" perché servono dati
// aggiornati (geocodifica, percorso, tile mappa) e funzionano comunque solo
// online: se falliscono, l'app deve continuare a funzionare senza bloccare nulla.
const NETWORK_FIRST_HOSTS = [
  'nominatim.openstreetmap.org',
  'router.project-osrm.org',
  'tile.openstreetmap.org'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(APP_SHELL.map((url) => cache.add(url).catch((err) => {
        console.log('Impossibile pre-cacheare (verrà cacheato al primo uso):', url, err);
      })))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  if (NETWORK_FIRST_HOSTS.some((host) => url.hostname === host || url.hostname.endsWith('.' + host))) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // Prezzi carburante (same-origin, aggiornato ogni giorno dalla GitHub Action):
  // network-first così mostra il valore più recente, con fallback all'ultimo noto
  // quando si è offline.
  if (url.pathname.endsWith('prezzi-carburante.json')) {
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response && response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => caches.match(event.request))
    );
    return;
  }

  // App shell locale + librerie esterne statiche (Leaflet): cache-first,
  // così il calcolatore e la mappa restano disponibili offline.
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (response && response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    }).catch(() => {
      if (event.request.mode === 'navigate') return caches.match('./index.html');
      return undefined;
    })
  );
});
