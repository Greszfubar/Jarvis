"""
THE GRESZ GAZETTE — Full broadsheet newspaper viewer sub-app.

Opens as a native pywebview window. Fetches the latest paper from the
Friday agent, parses ===SECTION:..=== markers, and renders a full
broadsheet layout.
"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>THE GRESZ GAZETTE</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --ink:#1a1208;
  --ink2:#2d2415;
  --paper:#f5f0e2;
  --paper2:#ede8d8;
  --paper3:#e4dfc8;
  --rule:#c8b89a;
  --rule2:#b09878;
  --gold:#9a7c3a;
  --red:#8b1a1a;
  --blue:#1a3a6b;
  --muted:#6b5a3e;
  --serif:'Georgia','Times New Roman',serif;
  --sans:'Helvetica Neue','Arial',sans-serif;
}

html,body{
  background:var(--paper);
  color:var(--ink);
  font-family:var(--serif);
  height:100%;
  overflow-x:hidden;
}

/* ── MASTHEAD ── */
#masthead{
  background:var(--ink);
  color:var(--paper);
  text-align:center;
  padding:0;
  border-bottom:4px solid var(--gold);
  user-select:none;
  -webkit-app-region:drag;
}
#mast-topline{
  font-family:var(--sans);
  font-size:9px;
  letter-spacing:3px;
  text-transform:uppercase;
  color:var(--rule);
  padding:8px 24px 4px;
  display:flex;
  justify-content:space-between;
  border-bottom:1px solid #333;
}
#mast-title{
  font-family:'Georgia',serif;
  font-size:clamp(36px,5vw,72px);
  font-weight:900;
  letter-spacing:-2px;
  line-height:1;
  padding:12px 24px 8px;
  text-transform:uppercase;
}
#mast-title span{color:var(--gold)}
#mast-dateline{
  font-family:var(--sans);
  font-size:10px;
  letter-spacing:2px;
  color:var(--rule);
  padding:6px 24px 10px;
  display:flex;
  justify-content:center;
  gap:32px;
  border-top:1px solid #333;
}

/* ── EDITION BAR ── */
#edition-bar{
  display:flex;
  gap:8px;
  padding:8px 24px;
  background:var(--paper2);
  border-bottom:2px solid var(--rule);
  overflow-x:auto;
  scrollbar-width:none;
  -webkit-app-region:no-drag;
}
#edition-bar::-webkit-scrollbar{display:none}
.ed-btn{
  flex-shrink:0;
  background:transparent;
  border:1px solid var(--rule2);
  padding:4px 12px;
  font-family:var(--sans);
  font-size:9px;
  letter-spacing:1px;
  text-transform:uppercase;
  color:var(--muted);
  cursor:pointer;
  border-radius:2px;
}
.ed-btn.active{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.ed-btn:hover:not(.active){background:var(--paper3)}

/* ── MAIN WRAPPER ── */
#paper-wrap{
  max-width:1360px;
  margin:0 auto;
  padding:24px 24px 60px;
}

/* ── LOADING / EMPTY ── */
#loading{
  text-align:center;
  padding:80px 24px;
  font-family:var(--sans);
  font-size:13px;
  letter-spacing:2px;
  color:var(--muted);
  text-transform:uppercase;
}
.spinner{
  width:32px;height:32px;
  border:3px solid var(--rule);
  border-top-color:var(--gold);
  border-radius:50%;
  margin:0 auto 16px;
  animation:spin 1s linear infinite;
}
@keyframes spin{to{transform:rotate(360deg)}}

/* ── HERO ── */
#hero{
  display:grid;
  grid-template-columns:1fr 340px;
  gap:0;
  border-bottom:3px double var(--rule2);
  margin-bottom:0;
}
#hero-main{
  padding:20px 24px 20px 0;
  border-right:1px solid var(--rule);
}
#hero-headline{
  font-size:clamp(28px,3.5vw,48px);
  font-weight:900;
  line-height:1.1;
  margin-bottom:12px;
  color:var(--ink);
}
#hero-subheadline{
  font-size:16px;
  font-style:italic;
  color:var(--ink2);
  margin-bottom:16px;
  line-height:1.5;
  border-left:3px solid var(--gold);
  padding-left:12px;
}
#editorial{
  font-size:14px;
  line-height:1.8;
  color:var(--ink2);
  max-width:68ch;
}
#hero-sidebar{
  padding:20px 0 20px 24px;
}
.side-section-label{
  font-family:var(--sans);
  font-size:8px;
  letter-spacing:3px;
  text-transform:uppercase;
  color:var(--gold);
  border-bottom:1px solid var(--rule);
  padding-bottom:6px;
  margin-bottom:12px;
}
.side-story{
  margin-bottom:14px;
  padding-bottom:14px;
  border-bottom:1px solid var(--rule);
}
.side-story:last-child{border-bottom:none}
.side-story-hed{
  font-size:13px;
  font-weight:700;
  line-height:1.3;
  margin-bottom:4px;
}
.side-story-body{
  font-size:11px;
  color:var(--muted);
  line-height:1.5;
}
.side-story-src{
  font-family:var(--sans);
  font-size:9px;
  color:var(--gold);
  letter-spacing:1px;
  text-transform:uppercase;
  margin-top:4px;
}

/* ── SECTION GRID ── */
#sections{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:0;
  border-top:2px solid var(--rule);
}
.section-col{
  padding:20px 20px 20px 0;
  border-right:1px solid var(--rule);
}
.section-col:last-child{border-right:none;padding-right:0}
.section-label{
  font-family:var(--sans);
  font-size:8px;
  font-weight:700;
  letter-spacing:3px;
  text-transform:uppercase;
  color:var(--paper);
  background:var(--ink);
  padding:4px 8px;
  margin-bottom:14px;
  display:inline-block;
}
.section-label.ai{background:#1a3a6b}
.section-label.one-piece{background:#8b1a1a}
.section-label.automation{background:#2d6b2d}
.section-label.aios{background:#4a1a6b}
.section-label.liam{background:#6b3a1a}

.story{
  margin-bottom:18px;
  padding-bottom:18px;
  border-bottom:1px solid var(--rule);
}
.story:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0}
.story-hed{
  font-size:15px;
  font-weight:700;
  line-height:1.3;
  margin-bottom:6px;
  color:var(--ink);
}
.story-body{
  font-size:12.5px;
  line-height:1.7;
  color:var(--ink2);
}
.story-src{
  font-family:var(--sans);
  font-size:9px;
  color:var(--muted);
  letter-spacing:1px;
  text-transform:uppercase;
  margin-top:6px;
  opacity:0.7;
}

/* ── QUOTE RULE ── */
#quote-section{
  border-top:3px double var(--rule2);
  border-bottom:3px double var(--rule2);
  padding:20px 24px;
  margin:8px 0;
  text-align:center;
}
#quote-text{
  font-size:20px;
  font-style:italic;
  color:var(--ink2);
  line-height:1.5;
  max-width:70ch;
  margin:0 auto 8px;
}
#quote-attr{
  font-family:var(--sans);
  font-size:10px;
  letter-spacing:2px;
  text-transform:uppercase;
  color:var(--gold);
}

/* ── FOOTER ── */
#footer{
  text-align:center;
  padding:16px;
  font-family:var(--sans);
  font-size:9px;
  letter-spacing:2px;
  text-transform:uppercase;
  color:var(--muted);
  border-top:2px solid var(--rule);
  margin-top:32px;
}

/* ── GENERATE BTN ── */
#gen-wrap{
  position:fixed;
  bottom:24px;right:24px;
  z-index:100;
}
#gen-btn{
  background:var(--ink);
  color:var(--paper);
  border:2px solid var(--gold);
  padding:10px 20px;
  font-family:var(--sans);
  font-size:10px;
  letter-spacing:2px;
  text-transform:uppercase;
  cursor:pointer;
  border-radius:2px;
  transition:background .2s;
}
#gen-btn:hover{background:var(--ink2)}
#gen-btn:disabled{opacity:0.5;cursor:not-allowed}

@media(max-width:900px){
  #hero{grid-template-columns:1fr}
  #hero-sidebar{display:none}
  #sections{grid-template-columns:1fr}
  .section-col{border-right:none;border-bottom:1px solid var(--rule);padding:16px 0}
}
</style>
</head>
<body>

<div id="masthead">
  <div id="mast-topline">
    <span>EST. 2025 · GRESZTECH MEDIA</span>
    <span id="mast-date">—</span>
    <span>EDITION <span id="mast-edition">—</span></span>
  </div>
  <div id="mast-title">The Gresz <span>Gazette</span></div>
  <div id="mast-dateline">
    <span>AI &amp; TECHNOLOGY</span>
    <span>·</span>
    <span>ONE PIECE</span>
    <span>·</span>
    <span>AUTOMATION</span>
    <span>·</span>
    <span>AiOS</span>
    <span>·</span>
    <span>LIAM OTTLEY</span>
  </div>
</div>

<div id="edition-bar"></div>

<div id="paper-wrap">
  <div id="loading">
    <div class="spinner"></div>
    Fetching today's edition…
  </div>
</div>

<div id="gen-wrap">
  <button id="gen-btn" onclick="generatePaper()">+ GENERATE NEW EDITION</button>
</div>

<script>
const BASE = 'http://127.0.0.1:8765';

let _papers = [];
let _current = 0;

// ── Date ──────────────────────────────────────────────────────────────────────
document.getElementById('mast-date').textContent =
  new Date().toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).toUpperCase();

// ── Load papers ───────────────────────────────────────────────────────────────
async function init(){
  // Use server-injected data if available (avoids fetch round-trip)
  if(window._serverPapers !== undefined){
    _papers = window._serverPapers;
  } else {
    try{
      const r = await fetch(`${BASE}/api/specialist/friday/papers`).then(r=>r.json());
      _papers = r.papers || [];
    }catch(e){
      _papers = [];
      console.error('Failed to load papers:', e);
    }
  }
  try{
    renderEditionBar();
    if(_papers.length) renderPaper(0);
    else showEmpty();
  }catch(e){
    console.error('Render error:', e);
    document.getElementById('paper-wrap').innerHTML = `
      <div id="loading" style="color:#8b1a1a">
        <div style="font-size:32px;margin-bottom:12px">⚠</div>
        Render error: ${esc(String(e))}<br>
        <button onclick="location.reload()" style="margin-top:16px;padding:8px 20px;background:#1a1208;color:#f5f0e2;border:1px solid #9a7c3a;cursor:pointer;font-family:sans-serif;font-size:10px;letter-spacing:2px">RELOAD</button>
      </div>`;
  }
}

function renderEditionBar(){
  const bar = document.getElementById('edition-bar');
  if(!_papers.length){ bar.innerHTML='<span style="font-size:10px;color:var(--muted);font-family:sans-serif;letter-spacing:1px">No editions yet — generate the first one</span>'; return; }
  bar.innerHTML = _papers.map((p,i)=>`
    <button class="ed-btn${i===0?' active':''}" onclick="renderPaper(${i})" id="ed-${i}">
      ${esc(p.date||'Edition '+(i+1))}
    </button>`).join('');
}

function renderPaper(idx){
  _current = idx;
  document.querySelectorAll('.ed-btn').forEach((b,i)=>{
    b.classList.toggle('active', i===idx);
  });
  const p = _papers[idx];
  if(!p){ showEmpty(); return; }
  document.getElementById('mast-edition').textContent = (_papers.length - idx);

  // Parse the structured content
  const parsed = parsePaper(p.content || '');
  renderParsed(p, parsed);
}

// ── Parser ────────────────────────────────────────────────────────────────────
function parsePaper(text){
  const result = {
    headline: '', subheadline: '', editorial: '', quote: '', sections: []
  };
  const lines = text.split('\\n');
  let mode = null;
  let sectionTitle = '';
  let sectionBuf = '';
  let storyBuf = '';

  function flushStory(){
    if(!storyBuf.trim() || !result.sections.length) return;
    const sec = result.sections[result.sections.length-1];
    const sLines = storyBuf.trim().split('\\n').filter(l=>l.trim());
    if(!sLines.length) return;
    let hed='', body='', src='';
    let bodyLines=[];
    sLines.forEach(l=>{
      if(l.startsWith('SOURCE:')) src = l.replace('SOURCE:','').trim();
      else if(!hed) hed = l.trim();
      else bodyLines.push(l.trim());
    });
    body = bodyLines.join(' ').trim();
    if(hed) sec.stories.push({hed, body, src});
    storyBuf = '';
  }

  function flushSection(){
    flushStory();
    if(mode === 'section' && sectionTitle){
      // already pushed on section start
    }
    sectionBuf = '';
  }

  for(let i=0; i<lines.length; i++){
    const line = lines[i];
    const trimmed = line.trim();

    if(trimmed === '===HEADLINE===')        { flushSection(); mode='headline'; continue; }
    if(trimmed === '===SUBHEADLINE===')     { flushSection(); mode='subheadline'; continue; }
    if(trimmed === '===EDITORIAL===')       { flushSection(); mode='editorial'; continue; }
    if(trimmed === '===QUOTE===')           { flushSection(); mode='quote'; continue; }
    if(trimmed.startsWith('===SECTION:')){
      flushSection();
      mode='section';
      sectionTitle = trimmed.replace('===SECTION:','').replace(/=+$/,'').trim();
      result.sections.push({title:sectionTitle, stories:[]});
      continue;
    }
    if(trimmed.startsWith('===') && trimmed.endsWith('===') && trimmed.length>6){
      flushSection(); mode=null; continue;
    }

    if(mode==='headline' && trimmed) result.headline += (result.headline?' ':'')+trimmed;
    else if(mode==='subheadline' && trimmed) result.subheadline += (result.subheadline?' ':'')+trimmed;
    else if(mode==='editorial') result.editorial += trimmed+' ';
    else if(mode==='quote') result.quote += trimmed+' ';
    else if(mode==='section'){
      if(trimmed==='STORY:'){ flushStory(); storyBuf=''; }
      else storyBuf += line + '\\n';
    }
  }
  flushSection();
  result.editorial = result.editorial.trim();
  result.quote = result.quote.trim();
  return result;
}

// ── Section colour map ────────────────────────────────────────────────────────
function sectionClass(title){
  const t = title.toLowerCase();
  if(t.includes('ai') || t.includes('machine')) return 'ai';
  if(t.includes('one piece') || t.includes('anime')) return 'one-piece';
  if(t.includes('automation') || t.includes('agent')) return 'automation';
  if(t.includes('aios') || t.includes('personal ai')) return 'aios';
  if(t.includes('liam') || t.includes('business')) return 'liam';
  return '';
}

// ── Render ─────────────────────────────────────────────────────────────────────
function renderParsed(p, parsed){
  const wrap = document.getElementById('paper-wrap');

  const heroSideSections = parsed.sections.slice(0,2);
  const bodySections     = parsed.sections.slice(2);

  // Hero sidebar: first 2 section first stories
  let sideHtml = '';
  heroSideSections.forEach(sec=>{
    if(!sec.stories.length) return;
    const st = sec.stories[0];
    sideHtml += `
      <div class="side-section-label">${esc(sec.title)}</div>
      ${sec.stories.slice(0,2).map(st=>`
        <div class="side-story">
          <div class="side-story-hed">${esc(st.hed)}</div>
          ${st.body?`<div class="side-story-body">${esc(st.body.slice(0,160))}…</div>`:''}
          ${st.src?`<div class="side-story-src">${esc(st.src)}</div>`:''}
        </div>`).join('')}`;
  });

  // Section columns for remaining sections
  let sectionHtml = '';
  bodySections.forEach(sec=>{
    const cls = sectionClass(sec.title);
    sectionHtml += `
      <div class="section-col">
        <div class="section-label ${cls}">${esc(sec.title)}</div>
        ${sec.stories.map(st=>`
          <div class="story">
            <div class="story-hed">${esc(st.hed)}</div>
            ${st.body?`<div class="story-body">${esc(st.body)}</div>`:''}
            ${st.src?`<div class="story-src">${esc(st.src)}</div>`:''}
          </div>`).join('')}
      </div>`;
  });

  // Also render hero-side sections (full stories) in body if > 2 sections
  if(heroSideSections.length){
    heroSideSections.forEach(sec=>{
      if(sec.stories.length<=1) return; // first story shown in sidebar
      const extra = sec.stories.slice(1);
      const cls = sectionClass(sec.title);
      sectionHtml = `
        <div class="section-col">
          <div class="section-label ${cls}">${esc(sec.title)} — continued</div>
          ${extra.map(st=>`
            <div class="story">
              <div class="story-hed">${esc(st.hed)}</div>
              ${st.body?`<div class="story-body">${esc(st.body)}</div>`:''}
              ${st.src?`<div class="story-src">${esc(st.src)}</div>`:''}
            </div>`).join('')}
        </div>` + sectionHtml;
    });
  }

  wrap.innerHTML = `
    <div id="hero">
      <div id="hero-main">
        <div id="hero-headline">${esc(parsed.headline || p.headline || 'Today\'s Edition')}</div>
        ${parsed.subheadline?`<div id="hero-subheadline">${esc(parsed.subheadline)}</div>`:''}
        ${parsed.editorial?`<div id="editorial">${esc(parsed.editorial)}</div>`:''}
      </div>
      <div id="hero-sidebar">
        ${sideHtml || '<div style="color:var(--muted);font-size:11px;font-family:sans-serif">No sidebar stories</div>'}
      </div>
    </div>
    ${parsed.quote?`
    <div id="quote-section">
      <div id="quote-text">${esc(parsed.quote)}</div>
    </div>`:''}
    <div id="sections">${sectionHtml}</div>
    <div id="footer">
      The Gresz Gazette · GreszTech Intelligence · ${esc(p.date||'')} · All rights reserved
    </div>`;
}

function showEmpty(){
  document.getElementById('paper-wrap').innerHTML = `
    <div id="loading">
      <div style="font-size:48px;margin-bottom:16px;opacity:.3">📰</div>
      No editions found.<br>
      <span style="font-size:10px">Click the button to generate today's paper.</span>
    </div>`;
}

// ── Generate ──────────────────────────────────────────────────────────────────
async function generatePaper(){
  const btn = document.getElementById('gen-btn');
  btn.textContent='GENERATING PAPER…'; btn.disabled=true;
  document.getElementById('paper-wrap').innerHTML=`
    <div id="loading">
      <div class="spinner"></div>
      Writing today's edition — this takes ~30 seconds…
    </div>`;
  try{
    const r = await fetch(`${BASE}/api/specialist/friday/papers/generate`,{
      method:'POST',headers:{'Content-Type':'application/json'},body:'{}'
    }).then(r=>r.json());
    if(r.paper){
      _papers.unshift(r.paper);
      try{
        renderEditionBar();
        renderPaper(0);
      }catch(re){
        document.getElementById('paper-wrap').innerHTML=`<div id="loading" style="color:#8b1a1a">Render error: ${esc(String(re))}</div>`;
      }
    } else {
      showEmpty();
    }
  }catch(e){
    document.getElementById('paper-wrap').innerHTML=`<div id="loading" style="color:#8b1a1a">Generation failed: ${esc(String(e))}</div>`;
  }
  btn.textContent='+ GENERATE NEW EDITION'; btn.disabled=false;
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
