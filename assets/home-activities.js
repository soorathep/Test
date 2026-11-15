/* Gallery feed is optional: the embedded same-site snapshot remains the fallback. */
(function () {
  'use strict';
  var figure = document.getElementById('home-activity');
  var template = document.getElementById('home-activity-albums');
  if (!figure || !template) return;
  var caption = figure.querySelector('[data-activity-caption]');
  var current;
  function choose(items) { return items[Math.floor(Math.random() * items.length)]; }
  function show(image, title, date) {
    image.decoding = 'async';
    image.setAttribute('fetchpriority', 'high');
    if (current) current.replaceWith(image);
    else figure.insertBefore(image, figure.firstChild);
    current = image;
    caption.textContent = title + (date ? ' · ' + date : '');
  }
  var localAlbums = Array.from(template.content.children).filter(function (a) { return a.querySelectorAll('img').length; });
  if (localAlbums.length) {
    var local = choose(localAlbums);
    show(choose(Array.from(local.querySelectorAll('img'))).cloneNode(true), local.dataset.title || '', local.dataset.date || '');
  }
  var base = 'https://soorathep.github.io/activities/';
  var controller = new AbortController();
  var timer = setTimeout(function () { controller.abort(); }, 4000);
  fetch(base + 'albums.json', {mode: 'cors', credentials: 'omit', cache: 'no-cache', signal: controller.signal})
    .then(function (response) { if (!response.ok) throw new Error('Gallery unavailable'); return response.json(); })
    .then(function (data) {
      if (!data || data.version !== 1 || !Array.isArray(data.albums) || data.albums.length > 2000) return;
      var albums = data.albums.filter(function (a) {
        return a && typeof a.title === 'string' && a.title.length <= 1000 &&
          (a.date == null || (typeof a.date === 'string' && a.date.length <= 200)) &&
          Array.isArray(a.photos) && a.photos.length <= 1000;
      }).map(function (a) {
        return {title: a.title, date: a.date || '', photos: a.photos.filter(function (p) {
          return typeof p === 'string' && p.length <= 255 && /^[^/\\\x00-\x1f]+\.(?:jpe?g|png|webp|gif|avif)$/i.test(p) && p !== '.' && p !== '..';
        })};
      }).filter(function (a) { return a.photos.length; });
      if (!albums.length) return;
      var album = choose(albums), image = new Image();
      image.alt = album.title;
      // Only install a fully loaded image; errors leave the local snapshot intact.
      image.onload = function () { show(image, album.title, album.date); };
      image.src = base + 'img/activities/' + encodeURIComponent(choose(album.photos));
    }).catch(function () { /* offline, CORS, timeout or invalid JSON: retain fallback */ })
    .finally(function () { clearTimeout(timer); });
})();
