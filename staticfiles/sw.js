// Gitako Service Worker for PWA and Offline Functionality
const CACHE_NAME = 'gitako-v1.0.0';
const OFFLINE_URL = '/offline/';

// Files to cache for offline functionality
const urlsToCache = [
  '/',
  '/dashboard/',
  '/calendar/',
  '/budget/',
  '/inventory/supplies/',
  '/offline/',
  // CSS files
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/7.0.0/mdb.min.css',
  'https://fonts.googleapis.com/icon?family=Material+Icons',
  'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap',
  // JS files
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/mdb-ui-kit/7.0.0/mdb.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js',
  // Static assets
  '/static/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', event => {
  console.log('Gitako SW: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Gitako SW: Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('Gitako SW: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Gitako SW: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Gitako SW: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Gitako SW: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Gitako SW: Activation complete');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // Handle navigation requests
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.open(CACHE_NAME)
            .then(cache => {
              return cache.match(OFFLINE_URL);
            });
        })
    );
    return;
  }

  // Handle other requests with cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request)
          .then(fetchResponse => {
            // Cache successful responses
            if (fetchResponse.status === 200) {
              const responseClone = fetchResponse.clone();
              caches.open(CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseClone);
                });
            }
            return fetchResponse;
          })
          .catch(() => {
            // Return offline page for failed requests
            if (event.request.destination === 'document') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Background sync for offline form submissions
self.addEventListener('sync', event => {
  console.log('Gitako SW: Background sync triggered', event.tag);
  
  if (event.tag === 'farm-data-sync') {
    event.waitUntil(syncFarmData());
  }
  
  if (event.tag === 'activity-sync') {
    event.waitUntil(syncActivities());
  }
  
  if (event.tag === 'budget-sync') {
    event.waitUntil(syncBudgetData());
  }
});

// Sync farm data when back online
async function syncFarmData() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['farmData'], 'readonly');
    const store = transaction.objectStore('farmData');
    const pendingData = await getAllRecords(store);
    
    for (const data of pendingData) {
      if (data.synced === false) {
        await syncDataToServer(data);
        // Mark as synced in IndexedDB
        const updateTransaction = db.transaction(['farmData'], 'readwrite');
        const updateStore = updateTransaction.objectStore('farmData');
        data.synced = true;
        updateStore.put(data);
      }
    }
    
    console.log('Gitako SW: Farm data sync completed');
  } catch (error) {
    console.error('Gitako SW: Farm data sync failed', error);
  }
}

// Sync activities when back online
async function syncActivities() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['activities'], 'readonly');
    const store = transaction.objectStore('activities');
    const pendingActivities = await getAllRecords(store);
    
    for (const activity of pendingActivities) {
      if (activity.synced === false) {
        await syncActivityToServer(activity);
        // Mark as synced
        const updateTransaction = db.transaction(['activities'], 'readwrite');
        const updateStore = updateTransaction.objectStore('activities');
        activity.synced = true;
        updateStore.put(activity);
      }
    }
    
    console.log('Gitako SW: Activities sync completed');
  } catch (error) {
    console.error('Gitako SW: Activities sync failed', error);
  }
}

// Sync budget data when back online
async function syncBudgetData() {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(['budgetData'], 'readonly');
    const store = transaction.objectStore('budgetData');
    const pendingBudgets = await getAllRecords(store);
    
    for (const budget of pendingBudgets) {
      if (budget.synced === false) {
        await syncBudgetToServer(budget);
        // Mark as synced
        const updateTransaction = db.transaction(['budgetData'], 'readwrite');
        const updateStore = updateTransaction.objectStore('budgetData');
        budget.synced = true;
        updateStore.put(budget);
      }
    }
    
    console.log('Gitako SW: Budget data sync completed');
  } catch (error) {
    console.error('Gitako SW: Budget data sync failed', error);
  }
}

// Helper functions for IndexedDB operations
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('GitakoOfflineDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      // Create object stores for offline data
      if (!db.objectStoreNames.contains('farmData')) {
        db.createObjectStore('farmData', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('activities')) {
        db.createObjectStore('activities', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('budgetData')) {
        db.createObjectStore('budgetData', { keyPath: 'id', autoIncrement: true });
      }
      
      if (!db.objectStoreNames.contains('inventoryData')) {
        db.createObjectStore('inventoryData', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

function getAllRecords(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

// Sync functions to server
async function syncDataToServer(data) {
  const response = await fetch('/api/sync/farm-data/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': await getCSRFToken()
    },
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    throw new Error(`Sync failed: ${response.statusText}`);
  }
  
  return response.json();
}

async function syncActivityToServer(activity) {
  const response = await fetch('/api/sync/activities/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': await getCSRFToken()
    },
    body: JSON.stringify(activity)
  });
  
  if (!response.ok) {
    throw new Error(`Activity sync failed: ${response.statusText}`);
  }
  
  return response.json();
}

async function syncBudgetToServer(budget) {
  const response = await fetch('/api/sync/budget/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': await getCSRFToken()
    },
    body: JSON.stringify(budget)
  });
  
  if (!response.ok) {
    throw new Error(`Budget sync failed: ${response.statusText}`);
  }
  
  return response.json();
}

// Get CSRF token for Django
async function getCSRFToken() {
  const response = await fetch('/api/csrf-token/');
  const data = await response.json();
  return data.csrfToken;
}

// Push notification handling
self.addEventListener('push', event => {
  console.log('Gitako SW: Push received', event);
  
  const options = {
    body: event.data ? event.data.text() : 'New farm activity reminder',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: 'View Details',
        icon: '/static/icons/icon-72x72.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icons/icon-72x72.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Gitako Farm Alert', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('Gitako SW: Notification click received', event);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/dashboard/')
    );
  }
});

console.log('Gitako SW: Service Worker loaded successfully');