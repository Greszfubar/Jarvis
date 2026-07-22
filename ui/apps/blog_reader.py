"""
GRESZ BLOG READER — Full-screen immersive blog post reader sub-app.

Opens as a native pywebview window.
URL: /blog?id=<blog_id>
Fetches the post from Friday agent and renders a beautiful reading experience.
"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GRESZ BLOG</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0a0f;
  --bg2:#111118;
  --bg3:#181820;
  --text:#e8e4f0;
  --text2:#b8b4c8;
  --muted:#6a6878;
  --accent:#7c5cfc;
  --accent2:#a08cff;
  --gold:#c9a84c;
  --rule:#2a2838;
  --serif:'Georgia','Times New Roman',serif;
  --sans:'Helvetica Neue','Arial',sans-serif;
  --mono:'SF Mono','Fira Code','Consolas',monospace;
}

html,body{
  background:var(--bg);
  color:var(--text);
  font-family:var(--serif);
  min-height:100%;
}

/* ── TOPBAR ── */
#topbar{
  position:fixed;top:0;left:0;right:0;z-index:100;
  background:rgba(10,10,15,0.92);
  backdrop-filter:blur(12px);
  border-bottom:1px solid var(--rule);
  padding:12px 32px;
  display:flex;align-items:center;justify-content:space-between;
  -webkit-app-region:drag;
}
#topbar-brand{
  font-family:var(--sans);
  font-size:10px;
  font-weight:700;
  letter-spacing:3px;
  text-transform:uppercase;
  color:var(--accent2);
}
#topbar-meta{
  font-family:var(--sans);
  font-size:10px;
  letter-spacing:1px;
  color:var(--muted);
  -webkit-app-region:no-drag;
}
#like-btn{
  background:transparent;
  border:1px solid var(--rule);
  color:var(--muted);
  padding:6px 16px;
  font-family:var(--sans);
  font-size:10px;
  letter-spacing:1px;
  cursor:pointer;
  border-radius:20px;
  transition:all .2s;
  -webkit-app-region:no-drag;
}
#like-btn:hover{border-color:var(--accent);color:var(--accent2)}
#like-btn.liked{background:var(--accent);border-color:var(--accent);color:#fff}

/* ── MAIN COLUMN ── */
#reader{
  max-width:720px;
  margin:0 auto;
  padding:100px 32px 120px;
}

/* ── HEADER ── */
#post-label{
  font-family:var(--sans);
  font-size:9px;
  font-weight:700;
  letter-spacing:3px;
  text-transform:uppercase;
  color:var(--accent2);
  margin-bottom:20px;
}
#post-title{
  font-size:clamp(28px,4vw,48px);
  font-weight:900;
  line-height:1.15;
  color:var(--text);
  margin-bottom:20px;
  letter-spacing:-0.5px;
}
#post-byline{
  font-family:var(--sans);
  font-size:12px;
  color:var(--muted);
  margin-bottom:12px;
  display:flex;
  gap:20px;
  align-items:center;
  flex-wrap:wrap;
}
#post-byline span{display:flex;align-items:center;gap:6px}
#post-divider{
  border:none;
  border-top:2px solid var(--rule);
  margin:28px 0;
}

/* ── BODY ── */
#post-body{
  font-size:18px;
  line-height:1.85;
  color:var(--text2);
}
#post-body p{margin-bottom:1.4em}
#post-body h2{
  font-size:22px;
  font-weight:800;
  color:var(--text);
  margin:2.2em 0 0.7em;
  font-family:var(--sans);
  letter-spacing:-0.3px;
  border-left:3px solid var(--accent);
  padding-left:14px;
}
#post-body h3{
  font-size:17px;
  font-weight:700;
  color:var(--text);
  margin:1.8em 0 0.5em;
  font-family:var(--sans);
}
#post-body strong{color:var(--text);font-weight:700}
#post-body em{color:var(--accent2);font-style:italic}
#post-body code{
  font-family:var(--mono);
  font-size:14px;
  background:var(--bg3);
  border:1px solid var(--rule);
  padding:2px 6px;
  border-radius:3px;
  color:var(--accent2);
}
#post-body blockquote{
  border-left:3px solid var(--gold);
  padding:12px 20px;
  margin:1.5em 0;
  background:var(--bg2);
  border-radius:0 4px 4px 0;
  font-style:italic;
  color:var(--text);
}
#post-body ul,#post-body ol{
  margin:1em 0 1em 2em;
}
#post-body li{margin-bottom:0.4em}
#post-body hr{
  border:none;
  border-top:1px solid var(--rule);
  margin:2.5em 0;
}

/* ── LOADING ── */
#loading{
  text-align:center;
  padding:120px 32px;
  font-family:var(--sans);
  font-size:11px;
  letter-spacing:2px;
  text-transform:uppercase;
  color:var(--muted);
}
.spinner{
  width:32px;height:32px;
  border:2px solid var(--rule);
  border-top-color:var(--accent);
  border-radius:50%;
  margin:0 auto 20px;
  animation:spin 1s linear infinite;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── PROGRESS BAR ── */
#progress{
  position:fixed;top:0;left:0;height:2px;
  background:var(--accent);
  transition:width .1s;
  z-index:200;
}

/* ── FOOTER ── */
#post-footer{
  border-top:1px solid var(--rule);
  padding-top:32px;
  margin-top:48px;
  font-family:var(--sans);
  font-size:11px;
  color:var(--muted);
  letter-spacing:1px;
  text-align:center;
}
#post-footer strong{color:var(--accent2)}
</style>
</head>
<body>

<div id="progress"></div>

<div id="topbar">
  <div id="topbar-brand">Gresz Blog</div>
  <div id="topbar-meta" id="read-time">Loading…</div>
  <button id="like-btn" onclick="toggleLike()">♡ Like</button>
</div>

<div id="reader">
  <div id="loading">
    <div class="spinner"></div>
    Loading article…
  </div>
</div>

<script>
const BASE = 'http://127.0.0.1:8765';

// ── Progress bar ──────────────────────────────────────────────────────────────
window.addEventListener('scroll', ()=>{
  const pct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight) * 100;
  document.getElementById('progress').style.width = Math.min(100,pct||0)+'%';
});

// ── Get blog ID from query string ─────────────────────────────────────────────
function getBlogId(){
  const p = new URLSearchParams(window.location.search);
  const raw = p.get('id');
  return raw ? parseInt(raw,10) : null;
}

// ── Liked state ───────────────────────────────────────────────────────────────
let _liked = false;
function toggleLike(){
  _liked = !_liked;
  const btn = document.getElementById('like-btn');
  btn.textContent = _liked ? '♥ Liked' : '♡ Like';
  btn.classList.toggle('liked', _liked);
  if(_liked) btn.style.transform='scale(1.1)';
  setTimeout(()=>btn.style.transform='', 150);
  // Persist in localStorage
  const id = getBlogId();
  if(id){
    const likes = JSON.parse(localStorage.getItem('blog_likes')||'{}');
    if(_liked) likes[id]=true; else delete likes[id];
    localStorage.setItem('blog_likes', JSON.stringify(likes));
  }
}

// ── Simple markdown renderer ──────────────────────────────────────────────────
function renderMarkdown(text){
  // Process line by line
  const lines = text.split('\\n');
  let html = '';
  let inList = false;
  let listTag = '';

  for(let i=0; i<lines.length; i++){
    let l = lines[i];

    // Headings
    if(l.startsWith('## ')){
      if(inList){ html+=`</${listTag}>`; inList=false; }
      html += `<h2>${inline(l.slice(3))}</h2>`;
      continue;
    }
    if(l.startsWith('### ')){
      if(inList){ html+=`</${listTag}>`; inList=false; }
      html += `<h3>${inline(l.slice(4))}</h3>`;
      continue;
    }
    if(l.startsWith('# ')){
      if(inList){ html+=`</${listTag}>`; inList=false; }
      html += `<h2>${inline(l.slice(2))}</h2>`;
      continue;
    }

    // HR
    if(/^---+$/.test(l.trim()) || /^===+$/.test(l.trim())){
      if(inList){ html+=`</${listTag}>`; inList=false; }
      html += '<hr>';
      continue;
    }

    // Blockquote
    if(l.startsWith('> ')){
      if(inList){ html+=`</${listTag}>`; inList=false; }
      html += `<blockquote>${inline(l.slice(2))}</blockquote>`;
      continue;
    }

    // Unordered list
    if(/^[*\-] /.test(l)){
      if(!inList || listTag!=='ul'){ if(inList) html+=`</${listTag}>`; html+='<ul>'; inList=true; listTag='ul'; }
      html += `<li>${inline(l.slice(2))}</li>`;
      continue;
    }

    // Ordered list
    if(/^\d+\. /.test(l)){
      if(!inList || listTag!=='ol'){ if(inList) html+=`</${listTag}>`; html+='<ol>'; inList=true; listTag='ol'; }
      html += `<li>${inline(l.replace(/^\d+\. /,''))}</li>`;
      continue;
    }

    if(inList){ html+=`</${listTag}>`; inList=false; }

    // Empty line
    if(!l.trim()){
      html += '';
      continue;
    }

    // Paragraph
    html += `<p>${inline(l)}</p>`;
  }
  if(inList) html+=`</${listTag}>`;
  return html;
}

function inline(s){
  // Bold
  s = s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  // Italic
  s = s.replace(/\*(.+?)\*/g,'<em>$1</em>');
  s = s.replace(/_(.+?)_/g,'<em>$1</em>');
  // Code
  s = s.replace(/`(.+?)`/g,'<code>$1</code>');
  // Escape remaining
  return s;
}

// ── Load post ─────────────────────────────────────────────────────────────────
async function init(){
  const id = getBlogId();
  try{
    let blog;
    if(id){
      const r = await fetch(`${BASE}/api/specialist/friday/blogs/${id}`).then(r=>r.json());
      blog = r.blog;
    }
    if(!blog){
      // Fallback: load latest
      const r = await fetch(`${BASE}/api/specialist/friday/blogs`).then(r=>r.json());
      const blogs = r.blogs || [];
      blog = blogs[0];
    }
    if(!blog){ showEmpty(); return; }

    // Check liked
    const likes = JSON.parse(localStorage.getItem('blog_likes')||'{}');
    if(likes[blog.id]){
      _liked = true;
      const btn=document.getElementById('like-btn');
      btn.textContent='♥ Liked';btn.classList.add('liked');
    }

    // Render
    const words = blog.words || (blog.content||'').split(/\\s+/).length;
    const readMins = Math.max(1, Math.round(words/230));
    document.getElementById('topbar-meta').textContent = `${words.toLocaleString()} words · ${readMins} min read`;
    document.title = blog.title + ' — Gresz Blog';

    const reader = document.getElementById('reader');
    const statusColor = {published:'#2d6b2d',draft:'#6b3a1a',scheduled:'#1a3a6b'}[blog.status]||'#444';
    reader.innerHTML = `
      <div id="post-label">GreszTech Editorial</div>
      <h1 id="post-title">${esc(blog.title)}</h1>
      <div id="post-byline">
        <span>✦ FRIDAY AI</span>
        <span>📅 ${esc(blog.created||'')}</span>
        <span>📖 ${readMins} min read</span>
        <span style="background:${statusColor};padding:2px 8px;border-radius:2px;font-size:9px;letter-spacing:1px;color:#fff;text-transform:uppercase">${esc(blog.status||'')}</span>
      </div>
      <hr id="post-divider">
      <div id="post-body">${renderMarkdown(blog.content||'')}</div>
      <div id="post-footer">
        <strong>The Gresz Gazette</strong> · GreszTech Intelligence · All Rights Reserved
      </div>`;
  }catch(e){
    document.getElementById('reader').innerHTML=`<div id="loading" style="color:#8b1a1a">Failed to load post: ${e}</div>`;
  }
}

function showEmpty(){
  document.getElementById('reader').innerHTML=`
    <div id="loading">
      <div style="font-size:40px;margin-bottom:16px;opacity:.3">✍️</div>
      No blog post found.
    </div>`;
}

function esc(s){
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function openUrl(url){
  if(!url) return;
  fetch('http://127.0.0.1:8765/api/open_url',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({url})
  }).catch(()=>{ window.open(url,'_blank'); });
}

init();
</script>
</body>
</html>
"""
