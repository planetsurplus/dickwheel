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

// Motive Wheel banner: rotating quips + opens the pop-up (falls back to the /wheel/ page)
(function(){var link=document.querySelector(".wheel-banner"),dlg=document.getElementById("wheel-dialog");if(!link)return;
var sub=link.querySelector(".wb-sub"),q=(sub&&sub.dataset.quips||"").split("|").filter(Boolean),i=Math.floor(Math.random()*q.length);
if(sub&&q.length){sub.textContent=q[i];if(!matchMedia("(prefers-reduced-motion: reduce)").matches)setInterval(function(){sub.style.opacity=0;setTimeout(function(){i=(i+1)%q.length;sub.textContent=q[i];sub.style.opacity=1},350)},4200)}
if(!dlg||!dlg.showModal)return;var fr=dlg.querySelector(".wheel-embed");
function close(){dlg.close();link.focus()}
link.addEventListener("click",function(e){if(e.ctrlKey||e.metaKey||e.shiftKey||e.button)return;e.preventDefault();if(!fr.getAttribute("src"))fr.setAttribute("src",fr.dataset.src);dlg.showModal()});
dlg.querySelector(".wheel-close").addEventListener("click",close);dlg.addEventListener("click",function(e){if(e.target===dlg)close()});})();

// share bar: copy link + native share sheet on phones
document.querySelectorAll(".share").forEach(function(bar){var url=bar.dataset.url,title=bar.dataset.title;
var copy=bar.querySelector(".copy"),nat=bar.querySelector(".native");
if(copy)copy.addEventListener("click",function(){var done=function(){copy.textContent="Copied!";setTimeout(function(){copy.textContent="Copy link"},1800)};
if(navigator.clipboard)navigator.clipboard.writeText(url).then(done,function(){prompt("Copy this link:",url)});else prompt("Copy this link:",url)});
if(nat&&navigator.share){nat.hidden=false;nat.addEventListener("click",function(){navigator.share({title:title,url:url}).catch(function(){})})}});

// Newer-edition check: an open tab, a stale cached page, or an old edition URL
// (e.g. one the address bar autocompleted) notices when a newer edition is out.
(function(){var m=document.querySelector("main[data-edition]");if(!m||!window.fetch)return;
var shown=m.dataset.edition,home=m.dataset.home==="1",base=document.body.dataset.base||"/",bar=null;
function check(){fetch(base+"latest.json?t="+Date.now(),{cache:"no-store"}).then(function(r){return r.ok?r.json():null}).then(function(d){
if(!d||!d.date||d.date<=shown)return;var url=base+"editions/"+d.date+"/";
if(home){location.replace(url);return}
if(bar)return;bar=document.createElement("a");bar.className="newer-bar";bar.href=url;
bar.innerHTML="<b>Newer edition out:</b> "+String(d.label||d.date).replace(/[<>&]/g,"")+" <span aria-hidden=\"true\">&rarr;</span>";
m.insertBefore(bar,m.firstChild)}).catch(function(){})}
check();document.addEventListener("visibilitychange",function(){if(!document.hidden)check()});
setInterval(function(){if(!document.hidden)check()},15*60*1000);})();
