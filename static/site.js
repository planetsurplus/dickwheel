(function () {
  // Theme toggle (remembered per browser)
  var root = document.documentElement;
  try { var t = localStorage.getItem('theme'); if (t) root.setAttribute('data-theme', t); } catch (e) {}
  document.querySelectorAll('.theme-toggle').forEach(function (b) {
    b.addEventListener('click', function () {
      var dark = root.getAttribute('data-theme') === 'dark' ||
        (!root.getAttribute('data-theme') && matchMedia('(prefers-color-scheme: dark)').matches);
      var next = dark ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  });

  // Category filters on edition pages
  var bar = document.querySelector('.filters');
  if (bar) {
    bar.addEventListener('click', function (e) {
      var btn = e.target.closest('button'); if (!btn) return;
      bar.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      var cat = btn.dataset.cat;
      document.querySelectorAll('.entries .entry').forEach(function (el) {
        el.hidden = cat !== 'all' && el.dataset.cat !== cat;
      });
    });
  }

  // Search page
  var box = document.getElementById('q');
  if (box) {
    var out = document.getElementById('results');
    var base = document.body.dataset.base || '/';
    var idx = [];
    fetch(base + 'search-index.json').then(function (r) { return r.json(); }).then(function (d) {
      idx = d; var q = new URLSearchParams(location.search).get('q'); if (q) { box.value = q; run(); }
    });
    function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; }); }
    function run() {
      var terms = box.value.toLowerCase().split(/\s+/).filter(Boolean);
      if (!terms.length) { out.innerHTML = ''; return; }
      var hits = idx.filter(function (e) { return terms.every(function (t) { return e.text.indexOf(t) !== -1; }); }).slice(0, 100);
      out.innerHTML = '<p class="presumption">' + hits.length + (hits.length === 100 ? '+' : '') + ' result' + (hits.length === 1 ? '' : 's') + '</p>' +
        hits.map(function (e) {
          return '<article class="entry"><div class="gutter"><span class="d">' + esc(e.date) + '</span><span>' + esc(e.agency) + '</span></div>' +
            '<div><h3><a href="' + base + e.url + '">' + esc(e.title) + '</a></h3><p>' + esc(e.snippet) + '</p></div></article>';
        }).join('');
    }
    box.addEventListener('input', run);
  }
})();

// size the Motive Wheel iframe to its content
addEventListener("message",function(e){var h=e.data&&e.data.dwWheelHeight;if(!h)return;document.querySelectorAll(".wheel-embed").forEach(function(f){if(f.contentWindow===e.source)f.style.height=Math.ceil(h)+"px"})});
