/* Service worker: lets the site work offline and installed as an app (PWA).
 *
 * - Every same-origin GET is answered from the cache at once, then re-checked with the server in the
 *   background (stale-while-revalidate). A changed data or code file is stored for the next open, and the
 *   page is told so it can offer "มีข้อมูลใหม่ แตะเพื่อโหลดใหม่".
 * - data/overlay.json (back-end edits) goes to the network first, the cache only when offline.
 * - CORE is cached when the worker installs; the rest of the data (index letters, tables, guides) is
 *   fetched in the background after that, so the whole site works offline (~2.8 MB compressed).
 * - Bump VERSION when this file's lists or strategy change. Data updates need no bump.
 * - scripts/check_data.py checks that every file listed here exists.
 */
var VERSION = 'v1';
var CACHE = 'icd-search-' + VERSION;

var CORE = [
  './',
  'index.html',
  'manifest.webmanifest',
  'assets/app.js',
  'assets/app.css',
  'assets/fonts/fonts.css',
  'assets/fonts/ibm-plex-sans-thai-thai-400-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-thai-500-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-thai-600-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-latin-400-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-latin-500-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-latin-600-normal.woff2',
  'assets/fonts/ibm-plex-mono-latin-500-normal.woff2',
  'assets/fonts/ibm-plex-mono-latin-600-normal.woff2',
  'assets/icons/icon-192.png',
  'assets/icons/favicon.svg',
  'data/icd10/codes.json',
  'data/icd9/codes.json',
  'data/shared/abbr.json',
  'data/shared/guidelines.json',
  'data/shared/feedback.json'
];
var REST = [
  'assets/admin.js',
  'assets/admin.css',
  'assets/fonts/ibm-plex-sans-thai-latin-ext-400-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-latin-ext-500-normal.woff2',
  'assets/fonts/ibm-plex-sans-thai-latin-ext-600-normal.woff2',
  'assets/fonts/ibm-plex-mono-latin-ext-500-normal.woff2',
  'assets/fonts/ibm-plex-mono-latin-ext-600-normal.woff2',
  'data/manifest.json',
  'data/icd10/keywords.json',
  'data/icd10/tables.json',
  'data/icd10/morph.json',
  'data/icd9/keywords.json',
  'data/shared/scg2026.json',
  'data/shared/nhso2562.json',
  'data/shared/guide.json',
  'data/icd10/index/manifest.json',
  'data/icd9/index/manifest.json'
];
// index letter files are listed in each index manifest: {"letters": {"I": {"A": 5665, ...}, "II": {...}}}
var INDEX_DIRS = ['data/icd10/index/', 'data/icd9/index/'];
// files whose change is worth telling the page about
var NOTIFY = /(\/|index\.html|\/assets\/app\.(js|css)|\/data\/.+\.json)$/;

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(CORE); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf('icd-search-') === 0 && k !== CACHE; })
      .map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }).then(cacheRest));
});

self.addEventListener('message', function (e) {
  if (e.data === 'cache-all') e.waitUntil(cacheRest());
  if (e.data === 'skip-waiting') self.skipWaiting();
});

// fetch what is not cached yet; ignore failures (offline, a file removed later)
function cacheRest() {
  return caches.open(CACHE).then(function (c) {
    var add = function (url) {
      return c.match(url).then(function (hit) {
        if (hit) return hit;
        return fetch(url).then(function (r) { if (r.ok) return c.put(url, r.clone()).then(function () { return r; }); });
      }).catch(function () {});
    };
    return Promise.all(REST.map(add)).then(function () {
      return Promise.all(INDEX_DIRS.map(function (dir) {
        return c.match(dir + 'manifest.json').then(function (r) { return r ? r.json() : null; }).then(function (m) {
          if (!m || !m.letters) return;
          var files = [];
          Object.keys(m.letters).forEach(function (sec) { Object.keys(m.letters[sec]).forEach(function (L) { files.push(dir + sec + '-' + L + '.json'); }); });
          return Promise.all(files.map(add));
        }).catch(function () {});
      }));
    });
  });
}

function notify(url) {
  self.clients.matchAll({ type: 'window' }).then(function (cs) {
    cs.forEach(function (cl) { cl.postMessage({ type: 'icd-updated', url: url }); });
  });
}

// a response changed when its ETag (or, without one, its size) differs from the cached copy
function changed(oldR, newR) {
  var a = oldR.headers.get('etag'), b = newR.headers.get('etag');
  if (a && b) return a !== b;
  var la = oldR.headers.get('content-length'), lb = newR.headers.get('content-length');
  return !!(la && lb && la !== lb);
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  var scope = self.registration.scope;
  if (req.url.indexOf(scope) !== 0) return;

  // back-end overlay: always try the network (the page adds ?v= to bypass caches)
  if (url.pathname.slice(-13) === '/overlay.json') {
    var key = scope + 'data/overlay.json';
    e.respondWith(fetch(req).then(function (r) {
      if (r.ok) { var copy = r.clone(); caches.open(CACHE).then(function (c) { c.put(key, copy); }); }
      return r;
    }).catch(function () { return caches.match(key); }));
    return;
  }

  // pages: the app is one page (index.html, views in the #hash)
  var isPage = req.mode === 'navigate';
  var key2 = isPage ? scope + 'index.html' : req;

  e.respondWith(caches.open(CACHE).then(function (c) {
    return c.match(key2, { ignoreSearch: isPage }).then(function (hit) {
      var net = fetch(isPage ? key2 : req, { cache: 'no-cache' }).then(function (r) {
        if (r.ok && r.type === 'basic') {
          if (hit && changed(hit, r) && NOTIFY.test(url.pathname)) notify(url.pathname);
          return c.put(key2, r.clone()).then(function () { return r; });
        }
        return r;
      });
      if (hit) { e.waitUntil(net.catch(function () {})); return hit; }
      return net;
    });
  }));
});
