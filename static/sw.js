/**
 * sw.js — WMS Service Worker
 * 策略：app shell 离线缓存（Network First，失败用缓存）
 * 不拦截 API（端口 8000）和 POST/PUT/DELETE 请求
 */
const CACHE = 'wms-shell-v1';
const SHELL  = ['/', '/static/index.html'];

/* ── 安装：预缓存 app shell ── */
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting())
  );
});

/* ── 激活：清理旧缓存版本 ── */
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

/* ── 请求拦截 ── */
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // 不拦截 API 调用（后端端口）
  if (url.port === '8000') return;
  // 不拦截写操作
  if (e.request.method !== 'GET') return;
  // 不拦截跨域（CDN）— 让浏览器正常处理
  if (url.origin !== self.location.origin) return;

  // Network First：先请求网络，失败则用缓存
  e.respondWith(
    fetch(e.request)
      .then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
