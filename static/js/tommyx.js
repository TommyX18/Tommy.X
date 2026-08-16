document.addEventListener('DOMContentLoaded', function () {
  // Page loader
  var loader = document.getElementById('pageLoader');
  if (loader) {
    setTimeout(function () { loader.classList.add('tx-loaded'); }, 300);
  }

  // Scroll reveal
  var revealEls = document.querySelectorAll('[data-aos]');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('tx-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('tx-in'); });
  }

  // Product gallery thumbnail switch
  var thumbs = document.querySelectorAll('.tx-pd-thumb');
  var mainImg = document.getElementById('txPdMainImg');
  var mainWrap = document.getElementById('txPdMainWrap');
  thumbs.forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      thumbs.forEach(function (t) { t.classList.remove('active'); });
      thumb.classList.add('active');
      if (mainImg) mainImg.src = thumb.dataset.full;
    });
  });

  // Click-to-zoom
  if (mainWrap) {
    mainWrap.addEventListener('click', function () {
      mainWrap.classList.toggle('tx-zoomed');
    });
  }

  // Live search suggestions (client-side filter against a data list rendered in template, if present)
  var searchInput = document.getElementById('txSearchInput');
  var searchResults = document.getElementById('txSearchLive');
  if (searchInput && searchResults) {
    var items = Array.prototype.slice.call(searchResults.querySelectorAll('[data-name]'));
    searchInput.addEventListener('input', function () {
      var q = searchInput.value.trim().toLowerCase();
      items.forEach(function (item) {
        var name = item.dataset.name.toLowerCase();
        item.style.display = (!q || name.indexOf(q) !== -1) ? '' : 'none';
      });
    });
  }
});
