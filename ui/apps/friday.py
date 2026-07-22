"""FRIDAY — Content & Media specialist app HTML shell."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FRIDAY — GreszTech</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:    #0c0e14;
  --bg1:   #121520;
  --bg2:   #181c28;
  --panel: #141720;
  --blue:  #4488ff;
  --blue2: #66aaff;
  --blo:   rgba(68,136,255,.12);
  --border:#1a2040;
  --text:  #c8ccdc;
  --muted: #404868;
  --red:   #cc4444;
  --green: #44cc88;
  --yellow:#ccaa44;
  --ink:   #e8e4d8;
  --paper: #1a1c22;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Courier New',monospace;overflow:hidden}
#topbar{height:48px;display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;border-bottom:1px solid var(--border);background:var(--bg1);flex-shrink:0}
#topbar .logo{font-size:18px;font-weight:700;letter-spacing:4px;color:var(--blue);text-shadow:0 0 12px var(--blue)}
#topbar .subtitle{font-size:10px;color:var(--muted);letter-spacing:2px}
#topbar .status-row{display:flex;gap:12px;align-items:center}
.status-pill{font-size:10px;padding:3px 10px;border-radius:3px;border:1px solid;letter-spacing:1px}
.status-pill.online{border-color:var(--blue);color:var(--blue);background:var(--blo)}
.status-pill.offline{border-color:#555;color:#555}

#layout{display:flex;height:calc(100% - 48px);overflow:hidden}

/* ── LEFT: Newspapers ── */
#left{width:320px;flex-shrink:0;border-right:1px solid var(--border);
  display:flex;flex-direction:column;background:var(--bg1)}
.panel-header{padding:12px 16px;font-size:10px;letter-spacing:2px;color:var(--muted);
  border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.panel-header span{color:var(--blue);font-size:9px;cursor:pointer}
.panel-header span:hover{text-shadow:0 0 6px var(--blue)}

#papers-list{flex:1;overflow-y:auto;padding:8px}
.paper-card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
  margin-bottom:8px;overflow:hidden;cursor:pointer;transition:border-color .2s}
.paper-card:hover{border-color:var(--blue)}
.paper-masthead{background:var(--paper);padding:10px 12px;border-bottom:2px solid var(--blue)}
.paper-name{font-size:14px;font-weight:700;color:var(--ink);letter-spacing:2px;font-family:Georgia,serif}
.paper-date{font-size:9px;color:var(--muted);margin-top:2px}
.paper-headline{padding:10px 12px;font-size:12px;color:var(--text);line-height:1.5}
.paper-tags{padding:0 12px 10px;display:flex;gap:4px;flex-wrap:wrap}
.paper-tag{font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid var(--border);color:var(--muted)}

#gen-btn{margin:8px;padding:10px;background:var(--blue);border:none;
  color:#fff;cursor:pointer;border-radius:4px;font-family:inherit;font-size:11px;
  font-weight:700;letter-spacing:2px;transition:all .2s}
#gen-btn:hover{background:var(--blue2)}

/* ── CENTER: News Carousel + Blogs ── */
#center{flex:1;display:flex;flex-direction:column;background:var(--bg);overflow:hidden}

/* News carousel */
#news-section{flex-shrink:0;border-bottom:1px solid var(--border)}
.section-title{padding:12px 16px;font-size:10px;letter-spacing:2px;color:var(--muted);
  display:flex;justify-content:space-between;border-bottom:1px solid var(--border)}
#news-carousel{display:flex;gap:12px;padding:12px 16px;overflow-x:auto;
  scroll-snap-type:x mandatory}
#news-carousel::-webkit-scrollbar{height:3px}
#news-carousel::-webkit-scrollbar-track{background:transparent}
#news-carousel::-webkit-scrollbar-thumb{background:var(--border)}
.news-card{flex-shrink:0;width:240px;background:var(--bg2);border:1px solid var(--border);
  border-radius:4px;padding:12px;scroll-snap-align:start;cursor:pointer;transition:border-color .2s}
.news-card:hover{border-color:var(--blue)}
.news-source{font-size:9px;color:var(--blue);letter-spacing:1px;margin-bottom:6px}
.news-title{font-size:12px;color:var(--text);line-height:1.5;margin-bottom:6px}
.news-summary{font-size:10px;color:var(--muted);line-height:1.5}
.news-time{font-size:9px;color:var(--muted);margin-top:6px}

/* Blogs */
#blogs-section{flex:1;display:flex;flex-direction:column;overflow:hidden}
#blogs-list{flex:1;overflow-y:auto;padding:8px 16px}
.blog-item{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
  padding:12px;margin-bottom:8px;cursor:pointer;transition:border-color .2s}
.blog-item:hover{border-color:var(--blue)}
.blog-title{font-size:13px;color:var(--text);margin-bottom:4px}
.blog-meta{font-size:10px;color:var(--muted);display:flex;gap:12px}
.blog-status{font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid}
.blog-status.draft{border-color:var(--yellow);color:var(--yellow)}
.blog-status.published{border-color:var(--green);color:var(--green)}
.blog-status.scheduled{border-color:var(--blue);color:var(--blue)}

/* ── BOTTOM CMD ── */
#cmd-bar{height:50px;border-top:1px solid var(--border);background:var(--bg1);
  display:flex;align-items:center;padding:0 16px;gap:12px;flex-shrink:0}
#cmd-input{flex:1;background:transparent;border:1px solid var(--border);
  color:var(--text);padding:8px 12px;font-family:inherit;font-size:13px;
  border-radius:4px;outline:none}
#cmd-input:focus{border-color:var(--blue)}
#cmd-input::placeholder{color:var(--muted)}
#cmd-send{background:var(--blue);color:#fff;border:none;padding:8px 16px;
  border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px;font-weight:700;
  letter-spacing:1px}
#cmd-send:hover{background:var(--blue2)}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
@keyframes vpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.4)}}
</style>
</head>
<body>
<div id="topbar">
  <div>
    <div class="logo">⬡ FRIDAY</div>
    <div class="subtitle">CONTENT &amp; MEDIA — GRESZTECH LAYER 2</div>
  </div>
  <div class="status-row">
    <div id="voice-pill" style="display:none;align-items:center;gap:6px;background:rgba(59,130,246,.12);border:1px solid rgba(59,130,246,.4);border-radius:20px;padding:3px 10px;font-size:9px;letter-spacing:1px;color:#60a5fa">
      <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#60a5fa;animation:vpulse 1.2s ease-in-out infinite"></span>
      VOICE ACTIVE
    </div>
    <div class="status-pill online" id="agent-status">● ONLINE</div>
    <div class="status-pill offline" id="news-status">◌ NEWS FEED</div>
    <div style="font-size:10px;color:var(--muted)" id="clock"></div>
  </div>
</div>

<div id="layout">
  <!-- LEFT: Newspapers -->
  <div id="left">
    <div class="panel-header">
      NEWSPAPERS
      <span onclick="generatePaper()">+ GENERATE</span>
    </div>
    <div id="papers-list"></div>
    <button id="gen-btn" onclick="generatePaper()">GENERATE DAILY PAPER</button>
  </div>

  <!-- CENTER -->
  <div id="center">
    <!-- News -->
    <div id="news-section">
      <div class="section-title">
        NEWS FEED
        <span style="color:var(--blue);cursor:pointer;font-size:9px" onclick="loadNews()">↻ REFRESH</span>
      </div>
      <div id="news-carousel">
        <div style="color:var(--muted);font-size:11px;padding:20px">Loading news…</div>
      </div>
    </div>

    <!-- Blogs -->
    <div id="blogs-section">
      <div class="section-title">
        BLOG POSTS
        <span style="color:var(--blue);cursor:pointer;font-size:9px" onclick="newBlog()">+ NEW</span>
      </div>
      <div id="blogs-list"></div>
    </div>

    <div id="cmd-bar">
      <input id="cmd-input" placeholder="Ask FRIDAY to write, research, generate content…" onkeydown="cmdKey(event)">
      <button id="cmd-send" onclick="sendCmd()">SEND</button>
    </div>
  </div>
</div>

<script>
const BASE = 'http://127.0.0.1:8765';
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

// Open URL in system browser — routes through backend since sub-app windows
// don't have pywebview js_api attached
function openUrl(url){
  if(!url) return;
  fetch('http://127.0.0.1:8765/api/open_url',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({url})
  }).catch(()=>{ window.open(url,'_blank'); });
}

// Open newspaper window — via backend trigger (sub-app has no pywebview js_api)
function openNewspaper(){
  fetch('http://127.0.0.1:8765/api/open_app',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({app:'newspaper'})
  }).catch(console.error);
}

// Open blog reader window
function openBlogWindow(blogId){
  fetch('http://127.0.0.1:8765/api/open_app',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({app:'blog',id:blogId})
  }).catch(console.error);
}

// Clock
function tick(){
  const el=document.getElementById('clock');
  if(el) el.textContent=new Date().toLocaleTimeString('en-US',{hour12:false});
}
tick(); setInterval(tick,1000);

// ── VOICE INDICATOR ───────────────────────────────────────────────────────────
async function pollVoice(){
  try{
    const r=await fetch(`${BASE}/api/voice/active`).then(r=>r.json());
    const pill=document.getElementById('voice-pill');
    if(pill) pill.style.display = r.agent==='friday' ? 'flex' : 'none';
  }catch(_){}
}
pollVoice(); setInterval(pollVoice, 3000);

// ── NEWSPAPERS ────────────────────────────────────────────────────────────────
let _papers=[], _activePaper=null;

async function loadPapers(){
  try{
    const r=await fetch(`${BASE}/api/specialist/friday/papers`).then(r=>r.json());
    _papers=r.papers||[];
    renderPapers();
  }catch(_){ renderPapers(); }
}

function renderPapers(){
  const c=document.getElementById('papers-list');
  if(!_papers.length){
    c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:12px">No editions yet. Click GENERATE to create today\'s paper.</div>';
    return;
  }
  c.innerHTML=_papers.map((p,i)=>`
    <div class="paper-card${i===0?' active':''}" onclick="openNewspaper()" style="cursor:pointer">
      <div class="paper-masthead">
        <div class="paper-name">THE GRESZ GAZETTE</div>
        <div class="paper-date">${esc(p.date)}</div>
      </div>
      <div class="paper-headline">${esc((p.headline||p.content||'').slice(0,100))}</div>
      ${p.sources?.length?`<div class="paper-tags">${p.sources.slice(0,3).map(s=>`<span class="paper-tag">${esc(s)}</span>`).join('')}</div>`:''}
      <div style="font-size:9px;color:var(--blue);margin-top:6px;letter-spacing:1px">↗ OPEN FULL EDITION</div>
    </div>`).join('');
}

async function generatePaper(){
  const btn=document.getElementById('gen-btn');
  btn.textContent='GENERATING…';btn.disabled=true;
  try{
    const r=await fetch(`${BASE}/api/specialist/friday/papers/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json());
    if(r.paper){
      _papers.unshift(r.paper);
      renderPapers();
      // Auto-open the newspaper window
      setTimeout(openNewspaper, 500);
    }
  }catch(e){ alert('Generation failed: '+e); }
  btn.textContent='GENERATE DAILY PAPER';btn.disabled=false;
}

// ── NEWS CAROUSEL ─────────────────────────────────────────────────────────────
let _newsCategory='general';
const NEWS_CATS=['general','tech','business','science'];

async function loadNews(cat){
  cat=cat||_newsCategory;
  _newsCategory=cat;
  const c=document.getElementById('news-carousel');
  c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:20px;flex-shrink:0">Loading news…</div>';
  try{
    const r=await fetch(`${BASE}/api/specialist/friday/news?category=${cat}&count=10`).then(r=>r.json());
    const arts=r.articles||[];
    document.getElementById('news-status').textContent='● NEWS FEED';
    document.getElementById('news-status').className='status-pill online';
    if(!arts.length){
      c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:20px;flex-shrink:0">No news — add NEWSAPI_KEY in ULTRON Tool Vault.</div>';
      return;
    }
    c.innerHTML=arts.map(a=>`
      <div class="news-card" onclick="openUrl('${esc(a.url)}')" style="cursor:pointer">
        <div class="news-source">${esc(a.source||'RSS')}</div>
        <div class="news-title">${esc(a.title)}</div>
        <div class="news-summary">${esc(a.summary||'')}</div>
        <div class="news-time">${esc(a.time||'')}</div>
      </div>`).join('');
  }catch(_){
    c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:20px;flex-shrink:0">News unavailable.</div>';
  }
}

// Category filter row
function renderCatFilter(){
  const sec=document.getElementById('news-section');
  const hdr=sec.querySelector('.section-title');
  if(!hdr.querySelector('.cat-filters')){
    const div=document.createElement('div');div.className='cat-filters';
    div.style.cssText='display:flex;gap:6px;padding:4px 16px 8px';
    NEWS_CATS.forEach(c=>{
      const btn=document.createElement('button');
      btn.textContent=c.toUpperCase();
      btn.dataset.cat=c;
      btn.style.cssText='background:transparent;border:1px solid var(--border);color:var(--muted);padding:3px 8px;cursor:pointer;font-family:inherit;font-size:9px;letter-spacing:1px;border-radius:2px;transition:all .15s';
      btn.onclick=()=>{ document.querySelectorAll('.cat-filters button').forEach(b=>{ b.style.borderColor='var(--border)';b.style.color='var(--muted)'; }); btn.style.borderColor='var(--blue)';btn.style.color='var(--blue)'; loadNews(c); };
      div.appendChild(btn);
    });
    sec.insertBefore(div,sec.querySelector('#news-carousel'));
  }
}

// ── BLOGS ─────────────────────────────────────────────────────────────────────
let _blogs=[], _editingBlog=null;

async function loadBlogs(){
  try{
    const r=await fetch(`${BASE}/api/specialist/friday/blogs`).then(r=>r.json());
    _blogs=r.blogs||[];
    renderBlogs();
  }catch(_){ renderBlogs(); }
}

function renderBlogs(){
  const c=document.getElementById('blogs-list');
  if(!_blogs.length){
    c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:12px">No posts yet. Use the command bar to generate one.</div>';
    return;
  }
  c.innerHTML=_blogs.map((b,i)=>`
    <div class="blog-item">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px">
        <div class="blog-title" onclick="openBlogWindow(${b.id})" style="cursor:pointer;flex:1;color:var(--blue)" title="Click to open full reader">${esc(b.title)}</div>
        <span class="blog-status ${b.status||'draft'}">${(b.status||'DRAFT').toUpperCase()}</span>
      </div>
      <div class="blog-meta">
        <span>${esc(b.created||'')}</span>
        <span>${b.words||0} words · ${Math.max(1,Math.round((b.words||0)/230))} min read</span>
        <span onclick="openBlogWindow(${b.id})" style="cursor:pointer;color:var(--blue)">↗ OPEN</span>
        <span onclick="cycleBlogStatus(${i})" style="cursor:pointer;color:var(--muted)">STATUS</span>
        <span onclick="deleteBlog(${i})" style="cursor:pointer;color:var(--red)">DELETE</span>
      </div>
    </div>`).join('');
}

function editBlog(i){ _editingBlog=_editingBlog===i?null:i; renderBlogs(); }

async function saveBlogContent(i){
  const content=document.getElementById(`blog-content-${i}`)?.value||'';
  _blogs[i].content=content;
  _blogs[i].words=content.split(/\s+/).filter(Boolean).length;
  _editingBlog=null;
  await saveBlogs();
  renderBlogs();
}

async function cycleBlogStatus(i){
  const cycle=['draft','scheduled','published'];
  const cur=_blogs[i].status||'draft';
  _blogs[i].status=cycle[(cycle.indexOf(cur)+1)%cycle.length];
  await saveBlogs();
  renderBlogs();
}

async function deleteBlog(i){
  if(!confirm(`Delete "${_blogs[i].title}"?`))return;
  _blogs.splice(i,1);
  await saveBlogs();
  renderBlogs();
}

async function saveBlogs(){
  await fetch(`${BASE}/api/specialist/friday/blogs`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({blogs:_blogs})});
}

async function newBlog(){
  const t=prompt('Blog title:');if(!t)return;
  const gen=confirm('Generate AI draft? Takes ~30 seconds.\n(Cancel = blank post)');
  if(gen){
    const btn=document.getElementById('gen-btn');
    btn.textContent='DRAFTING…';btn.disabled=true;
    try{
      const r=await fetch(`${BASE}/api/specialist/friday/blogs`,{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({action:'generate',title:t})}).then(r=>r.json());
      if(r.blog){
        _blogs.unshift(r.blog);
        renderBlogs();
        // Auto-open the reader
        setTimeout(()=>openBlogWindow(r.blog.id), 500);
      }
    }catch(e){ alert('Generation failed: '+e); }
    btn.textContent='GENERATE DAILY PAPER';btn.disabled=false;
  } else {
    const newPost={id:Date.now(),title:t,content:'',status:'draft',words:0,created:new Date().toISOString().slice(0,10)};
    _blogs.unshift(newPost);
    await saveBlogs();
    renderBlogs();
    setTimeout(()=>openBlogWindow(newPost.id), 300);
  }
}

// ── COMMAND BAR ───────────────────────────────────────────────────────────────
// ── MARKDOWN RENDERER ─────────────────────────────────────────────────────────
function mdToHtml(t){
  t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/^### (.+)$/gm,'<div style="font-size:10px;letter-spacing:2px;color:var(--muted);margin:8px 0 3px;text-transform:uppercase">$1</div>');
  t=t.replace(/^## (.+)$/gm,'<div style="font-size:12px;color:var(--blue);letter-spacing:1px;margin:8px 0 4px">$1</div>');
  t=t.replace(/^# (.+)$/gm,'<div style="font-size:13px;font-weight:700;color:var(--blue);letter-spacing:2px;margin:8px 0 5px">$1</div>');
  t=t.replace(/\*\*(.+?)\*\*/g,'<strong style="color:var(--text)">$1</strong>');
  t=t.replace(/\*(.+?)\*/g,'<em style="color:var(--text)">$1</em>');
  t=t.replace(/`(.+?)`/g,'<code style="background:var(--bg1);padding:1px 5px;border-radius:2px;font-size:11px">$1</code>');
  t=t.replace(/^[-*•] (.+)$/gm,'<div style="padding-left:14px;margin:2px 0">· $1</div>');
  t=t.replace(/^\d+\. (.+)$/gm,'<div style="padding-left:14px;margin:2px 0">$1</div>');
  t=t.replace(/\n\n/g,'<br>').replace(/\n/g,'<br>');
  return t;
}

function cmdKey(e){if(e.key==='Enter')sendCmd();}
async function sendCmd(){
  const inp=document.getElementById('cmd-input');
  const text=inp.value.trim();if(!text)return;
  const orig=text; inp.value='';

  const lower=text.toLowerCase();

  // Local shortcuts
  if(lower.includes('news')){ loadNews(); return; }
  if(lower.includes('paper')||lower.includes('newspaper')){ generatePaper(); return; }
  if(lower.match(/write|blog|draft/)){
    const title=text.replace(/^(write|draft|blog|a blog about|an article about)\s*/i,'').trim()||'New Post';
    const r=await fetch(`${BASE}/api/specialist/friday/blogs`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action:'generate',title})}).then(r=>r.json()).catch(()=>({}));
    if(r.blog){
      _blogs.unshift(r.blog);
      renderBlogs();
      setTimeout(()=>openBlogWindow(r.blog.id), 500);
      return;
    }
  }

  // Fallback to JARVIS orchestrator
  try{
    const r=await fetch(`${BASE}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:'[FRIDAY] '+orig})});
    const d=await r.json();
    const reply=d.response||d.message||'Done.';
    // Show as a temp note
    const c=document.getElementById('blogs-list');
    const div=document.createElement('div');
    div.className='blog-item';
    div.style.borderLeft='3px solid var(--blue)';
    div.innerHTML=`<div style="font-size:9px;color:var(--blue);margin-bottom:4px;letter-spacing:1px">JARVIS</div><div style="font-size:12px;line-height:1.6">${mdToHtml(reply)}</div>`;
    c.prepend(div);
  }catch(e){console.error(e);}
}

// ── INIT ──────────────────────────────────────────────────────────────────────
loadPapers();
loadBlogs();
loadNews();
renderCatFilter();
setInterval(loadNews, 15*60*1000);
</script>
</body>
</html>"""
