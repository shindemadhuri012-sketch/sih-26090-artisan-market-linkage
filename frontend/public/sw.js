/**
 * SIH 26090: Progressive Web App Service Worker
 * Implements App Shell caching (CacheFirst) and directory data caching (StaleWhileRevalidate)
 * with NetworkOnly bypass for authenticated transactions and mutation endpoints.
 */

const STATIC_CACHE_NAME = 'sih26090-static-v1';
const DATA_CACHE_NAME = 'sih26090-data-v1';

// Static App Shell assets to pre-cache
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/artisan/products',
  '/artisan/rfqs',
  '/artisan/demand'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('Some static assets failed to pre-cache:', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== STATIC_CACHE_NAME && key !== DATA_CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // 1. Transactional & Mutation Endpoints -> NetworkOnly (Never generic cache)
  if (
    url.pathname.startsWith('/api/v1/auth') ||
    url.pathname.startsWith('/api/v1/sync') ||
    url.pathname.startsWith('/api/v1/rfqs') ||
    event.request.method !== 'GET'
  ) {
    event.respondWith(fetch(event.request));
    return;
  }

  // 2. Master Directory APIs -> StaleWhileRevalidate
  if (url.pathname.startsWith('/api/v1/crafts') || url.pathname.startsWith('/api/v1/craft-categories')) {
    event.respondWith(
      caches.open(DATA_CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          const fetchPromise = fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse.status === 200) {
                cache.put(event.request, networkResponse.clone());
              }
              return networkResponse;
            })
            .catch(() => cachedResponse);

          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  // 3. Static Bundles & Navigation Pages -> CacheFirst with network fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((networkResponse) => {
        if (
          networkResponse.status === 200 &&
          (url.pathname.startsWith('/_next/static') || url.pathname.endsWith('.js') || url.pathname.endsWith('.css'))
        ) {
          const responseToCache = networkResponse.clone();
          caches.open(STATIC_CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Return cached root if navigation request fails
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      });
    })
  );
});
