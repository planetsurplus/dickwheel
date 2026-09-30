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

// contact form: reason-specific prompts, send in place
(function(){var f=document.getElementById("contact-form");if(!f||!window.fetch)return;
var btn=f.querySelector(".cf-send"),st=f.querySelector(".cf-status"),msg=f.querySelector("#cf-msg");
var hints={"Correction":"What's wrong, and what should it say?","Update: dismissed or acquitted":"Case number and outcome. We'll check the court record and update the entry.",
"Hot Tip":"Spill it. What happened, where, and when?","Complaint":"Go ahead. Get it all out. Take your time.","Other":"What's on your mind?"};
var sends={"Hot Tip":"Send it hot","Complaint":"File my complaint"};
function sync(){var t=f.topic.value;msg.placeholder=hints[t]||"";btn.textContent=sends[t]||"Send message"}
f.addEventListener("change",function(e){if(e.target.name==="topic")sync()});sync();
f.addEventListener("submit",function(e){e.preventDefault();var t=f.topic.value;
f.querySelector('[name="subject"]').value="dickwheel.com: "+t;
btn.disabled=true;btn.textContent="Sending…";st.className="cf-status";st.textContent="";
fetch(f.action,{method:"POST",headers:{"Accept":"application/json"},body:new FormData(f)})
.then(function(r){return r.json()}).then(function(d){if(!d.success)throw new Error(d.message||"failed");
f.reset();st.className="cf-status ok";
st.textContent=t==="Complaint"?"Complaint received and filed. Thank you for your service.":t==="Hot Tip"?"Tip received. Handle with oven mitts.":"Sent. If you left an email, expect a reply within a few days.";})
.catch(function(){st.className="cf-status err";st.textContent="Your message didn't send. Check your connection and try again.";})
.finally(function(){btn.disabled=false;sync()})});})();
