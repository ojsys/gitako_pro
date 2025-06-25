// Gitako Offline Functionality
class GitakoOffline {
    constructor() {
        this.db = null;
        this.isOnline = navigator.onLine;
        this.pendingSyncs = [];
        this.init();
    }

    async init() {
        await this.initIndexedDB();
        this.setupEventListeners();
        this.checkOnlineStatus();
        
        // Register background sync if supported
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            this.setupBackgroundSync();
        }
    }

    // Initialize IndexedDB for offline storage
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('GitakoOfflineDB', 1);
            
            request.onerror = () => {
                console.error('Gitako: IndexedDB error', request.error);
                reject(request.error);
            };
            
            request.onsuccess = () => {
                this.db = request.result;
                console.log('Gitako: IndexedDB initialized');
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Farm data store
                if (!db.objectStoreNames.contains('farmData')) {
                    const farmStore = db.createObjectStore('farmData', { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    farmStore.createIndex('timestamp', 'timestamp', { unique: false });
                    farmStore.createIndex('synced', 'synced', { unique: false });
                }
                
                // Activities store
                if (!db.objectStoreNames.contains('activities')) {
                    const activityStore = db.createObjectStore('activities', { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    activityStore.createIndex('timestamp', 'timestamp', { unique: false });
                    activityStore.createIndex('synced', 'synced', { unique: false });
                }
                
                // Budget data store
                if (!db.objectStoreNames.contains('budgetData')) {
                    const budgetStore = db.createObjectStore('budgetData', { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    budgetStore.createIndex('timestamp', 'timestamp', { unique: false });
                    budgetStore.createIndex('synced', 'synced', { unique: false });
                }
                
                // Inventory data store
                if (!db.objectStoreNames.contains('inventoryData')) {
                    const inventoryStore = db.createObjectStore('inventoryData', { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    inventoryStore.createIndex('timestamp', 'timestamp', { unique: false });
                    inventoryStore.createIndex('synced', 'synced', { unique: false });
                }
                
                console.log('Gitako: IndexedDB stores created');
            };
        });
    }

    // Setup event listeners for online/offline detection
    setupEventListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateOnlineStatus();
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateOnlineStatus();
        });

        // Intercept form submissions for offline handling
        document.addEventListener('submit', (event) => {
            if (!this.isOnline && event.target.classList.contains('offline-capable')) {
                event.preventDefault();
                this.handleOfflineFormSubmission(event.target);
            }
        });
    }

    // Update UI based on online status
    updateOnlineStatus() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.style.display = this.isOnline ? 'none' : 'block';
        }

        // Update form states
        const offlineForms = document.querySelectorAll('.offline-capable');
        offlineForms.forEach(form => {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                if (this.isOnline) {
                    submitBtn.innerHTML = submitBtn.innerHTML.replace('Save Offline', 'Save');
                } else {
                    submitBtn.innerHTML = submitBtn.innerHTML.replace('Save', 'Save Offline');
                }
            }
        });

        // Show sync indicator if there are pending syncs
        this.updateSyncIndicator();
    }

    // Check initial online status
    checkOnlineStatus() {
        this.isOnline = navigator.onLine;
        this.updateOnlineStatus();
    }

    // Handle form submission when offline
    async handleOfflineFormSubmission(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Add metadata
        data.timestamp = new Date().toISOString();
        data.synced = false;
        data.formAction = form.action;
        data.formMethod = form.method || 'POST';

        // Determine data type based on form action
        let storeName = 'farmData';
        if (form.action.includes('calendar') || form.action.includes('activity')) {
            storeName = 'activities';
        } else if (form.action.includes('budget')) {
            storeName = 'budgetData';
        } else if (form.action.includes('inventory')) {
            storeName = 'inventoryData';
        }

        try {
            await this.saveToIndexedDB(storeName, data);
            this.showOfflineMessage('Data saved offline. Will sync when connection is restored.');
            
            // Register for background sync
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('farm-data-sync');
            }
            
            // Reset form
            form.reset();
            
        } catch (error) {
            console.error('Gitako: Failed to save offline data', error);
            this.showOfflineMessage('Failed to save data offline. Please try again.', 'error');
        }
    }

    // Save data to IndexedDB
    async saveToIndexedDB(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);
            
            request.onsuccess = () => {
                console.log(`Gitako: Data saved to ${storeName}`, data);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`Gitako: Failed to save to ${storeName}`, request.error);
                reject(request.error);
            };
        });
    }

    // Get pending data from IndexedDB
    async getPendingData(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index('synced');
            const request = index.getAll(false);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Sync pending data when back online
    async syncPendingData() {
        if (!this.isOnline) return;

        const stores = ['farmData', 'activities', 'budgetData', 'inventoryData'];
        let totalPending = 0;

        for (const storeName of stores) {
            try {
                const pendingData = await this.getPendingData(storeName);
                totalPending += pendingData.length;
                
                for (const data of pendingData) {
                    await this.syncDataItem(storeName, data);
                }
            } catch (error) {
                console.error(`Gitako: Failed to sync ${storeName}`, error);
            }
        }

        if (totalPending > 0) {
            this.showOfflineMessage(`Synced ${totalPending} items successfully.`, 'success');
        }

        this.updateSyncIndicator();
    }

    // Sync individual data item
    async syncDataItem(storeName, data) {
        try {
            const endpoint = this.getEndpointForStore(storeName);
            const response = await fetch(endpoint, {
                method: data.formMethod,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                // Mark as synced in IndexedDB
                await this.markAsSynced(storeName, data.id);
                console.log(`Gitako: Synced ${storeName} item`, data.id);
            } else {
                throw new Error(`Sync failed: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`Gitako: Failed to sync ${storeName} item`, error);
            throw error;
        }
    }

    // Mark data as synced in IndexedDB
    async markAsSynced(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const getRequest = store.get(id);
            
            getRequest.onsuccess = () => {
                const data = getRequest.result;
                if (data) {
                    data.synced = true;
                    const updateRequest = store.put(data);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = () => reject(updateRequest.error);
                } else {
                    resolve(); // Item not found, consider it synced
                }
            };
            
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    // Get endpoint for store type
    getEndpointForStore(storeName) {
        const endpoints = {
            'farmData': '/api/sync/farm-data/',
            'activities': '/api/sync/activities/',
            'budgetData': '/api/sync/budget/',
            'inventoryData': '/api/sync/inventory/'
        };
        return endpoints[storeName] || '/api/sync/general/';
    }

    // Get CSRF token
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Setup background sync
    async setupBackgroundSync() {
        if ('serviceWorker' in navigator) {
            const registration = await navigator.serviceWorker.ready;
            
            // Register sync events
            await registration.sync.register('farm-data-sync');
            console.log('Gitako: Background sync registered');
        }
    }

    // Show offline message to user
    showOfflineMessage(message, type = 'info') {
        // Create or update notification
        let notification = document.getElementById('offline-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'offline-notification';
            notification.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                max-width: 300px;
                padding: 15px;
                border-radius: 5px;
                color: white;
                font-weight: 500;
                z-index: 1060;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(notification);
        }

        // Set color based on type
        const colors = {
            'info': '#2196f3',
            'success': '#4caf50',
            'error': '#f44336',
            'warning': '#ff9800'
        };

        notification.style.backgroundColor = colors[type] || colors.info;
        notification.textContent = message;
        notification.style.opacity = '1';

        // Auto hide after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }

    // Update sync indicator
    async updateSyncIndicator() {
        if (!this.db) return;

        const stores = ['farmData', 'activities', 'budgetData', 'inventoryData'];
        let totalPending = 0;

        for (const storeName of stores) {
            try {
                const pendingData = await this.getPendingData(storeName);
                totalPending += pendingData.length;
            } catch (error) {
                console.error(`Gitako: Failed to count pending ${storeName}`, error);
            }
        }

        // Update sync indicator in UI
        const syncIndicator = document.getElementById('sync-indicator');
        if (syncIndicator) {
            if (totalPending > 0) {
                syncIndicator.style.display = 'block';
                syncIndicator.textContent = `${totalPending} items pending sync`;
            } else {
                syncIndicator.style.display = 'none';
            }
        }
    }

    // Get offline statistics
    async getOfflineStats() {
        const stores = ['farmData', 'activities', 'budgetData', 'inventoryData'];
        const stats = {};

        for (const storeName of stores) {
            try {
                const pendingData = await this.getPendingData(storeName);
                stats[storeName] = {
                    pending: pendingData.length,
                    lastUpdate: pendingData.length > 0 ? 
                        Math.max(...pendingData.map(item => new Date(item.timestamp).getTime())) : null
                };
            } catch (error) {
                stats[storeName] = { pending: 0, lastUpdate: null };
            }
        }

        return stats;
    }
}

// Initialize offline functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gitakoOffline = new GitakoOffline();
    console.log('Gitako: Offline functionality initialized');
});

// Export for use in other scripts
window.GitakoOffline = GitakoOffline;