// sw.js
const CACHE_NAME = 'guitar-tab-proxy-cache-v1';
const API_BASE = 'https://api.ultimate-guitar.com/api/v1';

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME));
});

self.addEventListener('fetch', event => {
  // Nur API-Anfragen abfangen
  if (event.request.url.includes('/proxy/')) {
    event.respondWith(handleApiRequest(event.request));
  }
});

async function handleApiRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  // Cache-first Strategie
  if (cachedResponse) return cachedResponse;
  
  try {
    // API-URL aus der Anfrage extrahieren
    const apiPath = request.url.split('/proxy/')[1];
    const apiUrl = `${API_BASE}/${apiPath}`;
    
    const response = await fetch(apiUrl, {
      headers: {
        'Authorization': `Bearer ${UG_API_KEY}`
      }
    });
    
    // Für zukünftige Anfragen im Cache speichern
    cache.put(request, response.clone());
    
    return response;
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Proxy error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}