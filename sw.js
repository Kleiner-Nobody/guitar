// sw.js
const CACHE_NAME = 'guitar-tab-proxy-cache-v1';
const UG_API_BASE = 'https://api.ultimate-guitar.com/api/v1';

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME));
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Nur Anfragen an /proxy/ abfangen
  if (url.pathname.startsWith('/proxy/')) {
    event.respondWith(handleApiRequest(event.request));
  }
});

async function handleApiRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Cache-first Strategie
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    // API-URL rekonstruieren
    const apiPath = request.url.split('/proxy/')[1];
    const apiUrl = `${UG_API_BASE}/${apiPath}`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    // Nur erfolgreiche Antworten cachen
    if (response.status === 200) {
      const clone = response.clone();
      cache.put(request, clone);
    }
    
    return response;
  } catch (error) {
    return new Response(JSON.stringify({ 
      error: 'Proxy error',
      message: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}