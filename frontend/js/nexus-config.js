/**
 * NEXUS FORGE — Dynamic API & WebSocket Configuration Hub
 * 
 * Automatically resolves backend endpoints across:
 * 1. Local Development (http://localhost:8000 & ws://localhost:8000)
 * 2. Cloud Production (Frontend on Vercel + Backend on Render)
 * 3. Custom user override saved in localStorage or window.__NEXUS_BACKEND_URL__
 */
(function() {
  'use strict';

  // Configurable Render backend default URL
  // If deployed to Vercel and no local override exists, this fallback is used:
  const DEFAULT_RENDER_BACKEND = 'https://nexus-forge-backend.onrender.com';

  function isLocalhost(hostname) {
    return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]' || hostname.endsWith('.local');
  }

  function getStoredBackendUrl() {
    try {
      return localStorage.getItem('nexus_backend_url') || '';
    } catch (e) {
      return '';
    }
  }

  function getBaseUrl() {
    // 1. Explicit user override from localStorage
    const stored = getStoredBackendUrl();
    if (stored && stored.trim()) {
      return stored.trim().replace(/\/+$/, '');
    }

    // 2. Window global variable injection (e.g. injected at deploy time)
    if (window.__NEXUS_BACKEND_URL__ && window.__NEXUS_BACKEND_URL__.trim()) {
      return window.__NEXUS_BACKEND_URL__.trim().replace(/\/+$/, '');
    }

    const host = window.location.hostname;
    const port = window.location.port;

    // 3. Localhost development detection
    if (isLocalhost(host)) {
      // If frontend is running on 5500, 3000, or 5173, point to backend on 8000
      if (port === '5500' || port === '3000' || port === '5173' || port === '8080') {
        return 'http://localhost:8000';
      }
      return window.location.origin;
    }

    // 4. Remote deployment (e.g. *.vercel.app, *.pages.dev, custom domain)
    // If running on a remote host, default to the Render backend URL
    return DEFAULT_RENDER_BACKEND;
  }

  function getWsBaseUrl() {
    const httpBase = getBaseUrl();
    if (httpBase.startsWith('https://')) {
      return httpBase.replace(/^https:\/\//i, 'wss://');
    }
    if (httpBase.startsWith('http://')) {
      return httpBase.replace(/^http:\/\//i, 'ws://');
    }
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${wsProto}//${window.location.host}`;
  }

  const NexusConfig = {
    DEFAULT_RENDER_BACKEND: DEFAULT_RENDER_BACKEND,

    getHttpBase: getBaseUrl,
    getWsBase: getWsBaseUrl,

    getApiUrl: function(path) {
      const cleanPath = path.startsWith('/') ? path : `/${path}`;
      return `${getBaseUrl()}${cleanPath}`;
    },

    getWsUrl: function(path) {
      const cleanPath = path.startsWith('/') ? path : `/${path}`;
      return `${getWsBaseUrl()}${cleanPath}`;
    },

    getBackendUrl: getBaseUrl,

    setBackendUrl: function(url) {
      try {
        if (!url || !url.trim()) {
          localStorage.removeItem('nexus_backend_url');
        } else {
          localStorage.setItem('nexus_backend_url', url.trim().replace(/\/+$/, ''));
        }
        window.dispatchEvent(new CustomEvent('nexus:backend-url-changed', { detail: { url: getBaseUrl() } }));
      } catch (e) {
        console.warn('[NexusConfig] Failed to save backend URL to localStorage:', e);
      }
    },

    isConfigured: function() {
      const url = getBaseUrl();
      return Boolean(url && url.trim().length > 0);
    },

    checkHealth: async function(timeoutMs = 8000) {
      const url = this.getApiUrl('/ping');
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const start = performance.now();
        const res = await fetch(url, { method: 'GET', signal: controller.signal });
        clearTimeout(timer);
        const elapsed = Math.round(performance.now() - start);
        return {
          ok: res.ok,
          status: res.status,
          latencyMs: elapsed,
          isRenderSleep: false
        };
      } catch (err) {
        clearTimeout(timer);
        // If aborted or connection refused, check if Render might be spinning up
        const isTimeout = err.name === 'AbortError';
        return {
          ok: false,
          error: err.message,
          isRenderSleep: isTimeout || err.message.includes('Failed to fetch')
        };
      }
    }
  };

  window.NexusConfig = NexusConfig;
})();
