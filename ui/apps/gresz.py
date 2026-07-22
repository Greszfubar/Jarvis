"""GRESZ INDUSTRIES — Business AiOS platform HTML shell."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GRESZ INDUSTRIES — AiOS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:    #08090f;
  --bg1:   #0d0f1a;
  --bg2:   #121524;
  --panel: #0f1120;
  --gold:  #c8a840;
  --gold2: #e8c860;
  --glo:   rgba(200,168,64,.10);
  --border:#1e2240;
  --text:  #c8cce0;
  --muted: #404868;
  --red:   #cc4444;
  --green: #44cc88;
  --blue:  #4488cc;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Courier New',monospace;overflow:hidden}
#topbar{height:48px;display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;border-bottom:1px solid var(--border);background:var(--bg1);flex-shrink:0}
#topbar .logo{font-size:18px;font-weight:700;letter-spacing:4px;color:var(--gold);text-shadow:0 0 12px var(--gold)}
#topbar .subtitle{font-size:10px;color:var(--muted);letter-spacing:2px}
#topbar .status-row{display:flex;gap:12px;align-items:center}
.status-pill{font-size:10px;padding:3px 10px;border-radius:3px;border:1px solid;letter-spacing:1px}
.status-pill.online{border-color:var(--gold);color:var(--gold);background:var(--glo)}
.status-pill.offline{border-color:#555;color:#555}

#layout{display:flex;height:calc(100% - 48px);overflow:hidden}

/* ── LEFT: KPIs ── */
#left{width:240px;flex-shrink:0;border-right:1px solid var(--border);
  display:flex;flex-direction:column;background:var(--bg1)}
.panel-header{padding:12px 16px;font-size:10px;letter-spacing:2px;color:var(--muted);
  border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.panel-header span{color:var(--gold);font-size:9px;cursor:pointer}

#kpi-grid{padding:12px;display:flex;flex-direction:column;gap:8px}
.kpi-card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;padding:12px}
.kpi-label{font-size:9px;color:var(--muted);letter-spacing:2px;margin-bottom:4px}
.kpi-value{font-size:22px;color:var(--gold);font-weight:700;margin-bottom:2px}
.kpi-delta{font-size:10px}
.kpi-delta.up{color:var(--green)}
.kpi-delta.down{color:var(--red)}

#nav-links{padding:12px;border-top:1px solid var(--border);display:flex;flex-direction:column;gap:4px}
.nav-link{padding:8px 12px;border-radius:4px;cursor:pointer;font-size:11px;
  color:var(--muted);letter-spacing:1px;transition:all .15s;border:1px solid transparent}
.nav-link:hover{color:var(--gold);border-color:var(--border);background:var(--bg2)}
.nav-link.active{color:var(--gold);border-color:var(--gold);background:var(--glo)}

/* ── CENTER: Main content area ── */
#center{flex:1;display:flex;flex-direction:column;overflow:hidden}

#center-scroll{flex:1;overflow-y:auto;padding:16px}

/* Project tracker */
.section-hdr{display:flex;justify-content:space-between;align-items:center;
  margin-bottom:12px}
.section-hdr h2{font-size:11px;letter-spacing:2px;color:var(--muted)}
.section-hdr button{background:transparent;border:1px solid var(--border);color:var(--muted);
  padding:4px 10px;border-radius:3px;cursor:pointer;font-family:inherit;font-size:10px;
  letter-spacing:1px}
.section-hdr button:hover{border-color:var(--gold);color:var(--gold)}

.proj-table{width:100%;border-collapse:collapse;margin-bottom:24px}
.proj-table th{font-size:9px;color:var(--muted);letter-spacing:2px;
  padding:8px 12px;border-bottom:1px solid var(--border);text-align:left}
.proj-table td{padding:10px 12px;border-bottom:1px solid var(--border);font-size:12px}
.proj-table tr:hover td{background:var(--bg2)}
.proj-status{font-size:9px;padding:2px 8px;border-radius:2px;border:1px solid;letter-spacing:1px}
.proj-status.active{border-color:var(--gold);color:var(--gold)}
.proj-status.complete{border-color:var(--green);color:var(--green)}
.proj-status.hold{border-color:#555;color:#555}
.proj-status.urgent{border-color:var(--red);color:var(--red)}
.progress-bar{height:4px;background:var(--border);border-radius:2px;width:80px;overflow:hidden}
.progress-fill{height:100%;background:var(--gold);border-radius:2px}

/* Client list */
.client-card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
  padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:16px;cursor:pointer}
.client-card:hover{border-color:var(--gold)}
.client-avatar{width:36px;height:36px;border-radius:50%;background:var(--bg);
  border:1px solid var(--border);display:flex;align-items:center;justify-content:center;
  font-size:14px;color:var(--gold)}
.client-name{font-size:13px;color:var(--text)}
.client-tier{font-size:9px;color:var(--muted);margin-top:2px;letter-spacing:1px}
.client-value{margin-left:auto;font-size:13px;color:var(--gold)}

/* ── RIGHT: Pipeline ── */
#right{width:280px;flex-shrink:0;border-left:1px solid var(--border);
  display:flex;flex-direction:column;background:var(--bg1)}
#pipeline-list{flex:1;overflow-y:auto;padding:8px}
.pipe-card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
  padding:10px 12px;margin-bottom:6px}
.pipe-company{font-size:12px;color:var(--text);margin-bottom:2px}
.pipe-value{font-size:11px;color:var(--gold)}
.pipe-stage{font-size:9px;margin-top:4px;letter-spacing:1px}
.pipe-stage.lead{color:var(--muted)}
.pipe-stage.qualified{color:var(--blue)}
.pipe-stage.proposal{color:var(--yellow, #ccaa44)}
.pipe-stage.closing{color:var(--green)}

/* ── BOTTOM CMD ── */
#cmd-bar{height:50px;border-top:1px solid var(--border);background:var(--bg1);
  display:flex;align-items:center;padding:0 16px;gap:12px;flex-shrink:0}
#cmd-input{flex:1;background:transparent;border:1px solid var(--border);
  color:var(--text);padding:8px 12px;font-family:inherit;font-size:13px;
  border-radius:4px;outline:none}
#cmd-input:focus{border-color:var(--gold)}
#cmd-input::placeholder{color:var(--muted)}
#cmd-send{background:var(--gold);color:#000;border:none;padding:8px 16px;
  border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px;font-weight:700;
  letter-spacing:1px}
#cmd-send:hover{background:var(--gold2)}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
@keyframes vpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.4)}}
</style>
</head>
<body>
<div id="topbar">
  <div>
    <div class="logo">⬡ GRESZ INDUSTRIES</div>
    <div class="subtitle">BUSINESS AIOS PLATFORM — GRESZTECH LAYER 2</div>
  </div>
  <div class="status-row">
    <div id="voice-pill" style="display:none;align-items:center;gap:6px;background:rgba(234,179,8,.1);border:1px solid rgba(234,179,8,.4);border-radius:20px;padding:3px 10px;font-size:9px;letter-spacing:1px;color:#fbbf24">
      <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#fbbf24;animation:vpulse 1.2s ease-in-out infinite"></span>
      VOICE ACTIVE
    </div>
    <div class="status-pill online" id="agent-status">● ONLINE</div>
    <div style="font-size:10px;color:var(--muted)" id="clock"></div>
  </div>
</div>

<div id="layout">
  <!-- LEFT: KPIs + Nav -->
  <div id="left">
    <div class="panel-header">BUSINESS METRICS</div>
    <div id="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">MONTHLY REVENUE</div>
        <div class="kpi-value" id="kpi-rev">—</div>
        <div class="kpi-delta up" id="kpi-rev-d">Loading…</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">ACTIVE CLIENTS</div>
        <div class="kpi-value" id="kpi-clients">—</div>
        <div class="kpi-delta" id="kpi-clients-d"></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">PIPELINE VALUE</div>
        <div class="kpi-value" id="kpi-pipe">—</div>
        <div class="kpi-delta" id="kpi-pipe-d"></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">OPEN TASKS</div>
        <div class="kpi-value" id="kpi-tasks">—</div>
        <div class="kpi-delta" id="kpi-tasks-d"></div>
      </div>
    </div>
    <div id="nav-links">
      <div class="nav-link active" onclick="showView('projects')">▸ PROJECTS</div>
      <div class="nav-link" onclick="showView('clients')">▸ CLIENTS</div>
      <div class="nav-link" onclick="showView('finance')">▸ FINANCE</div>
      <div class="nav-link" onclick="showView('reports')">▸ REPORTS</div>
    </div>
  </div>

  <!-- CENTER -->
  <div id="center">
    <div id="center-scroll">
      <!-- Projects view (default) -->
      <div id="view-projects">
        <div class="section-hdr">
          <h2>ACTIVE PROJECTS</h2>
          <button onclick="newProject()">+ NEW PROJECT</button>
        </div>
        <table class="proj-table">
          <thead>
            <tr><th>PROJECT</th><th>CLIENT</th><th>STATUS</th><th>PROGRESS</th><th>DUE</th></tr>
          </thead>
          <tbody id="proj-body"></tbody>
        </table>
      </div>
      <!-- Clients view (hidden) -->
      <div id="view-clients" style="display:none">
        <div class="section-hdr">
          <h2>CLIENT ROSTER</h2>
          <button onclick="newClient()">+ ADD CLIENT</button>
        </div>
        <div id="clients-list"></div>
      </div>
      <!-- Finance view (hidden) -->
      <div id="view-finance" style="display:none">
        <div class="section-hdr"><h2>FINANCE</h2></div>
        <div style="color:var(--muted);font-size:12px;padding:40px;text-align:center">
          Finance module — coming in Phase 4.
        </div>
      </div>
      <!-- Reports view (hidden) -->
      <div id="view-reports" style="display:none">
        <div class="section-hdr"><h2>REPORTS</h2></div>
        <div style="color:var(--muted);font-size:12px;padding:40px;text-align:center">
          Reports module — coming in Phase 4.
        </div>
      </div>
    </div>
    <div id="cmd-bar">
      <input id="cmd-input" placeholder="Ask GRESZ to pull reports, update projects, analyse revenue…" onkeydown="cmdKey(event)">
      <button id="cmd-send" onclick="sendCmd()">SEND</button>
    </div>
  </div>

  <!-- RIGHT: Pipeline -->
  <div id="right">
    <div class="panel-header">
      SALES PIPELINE
      <span onclick="newDeal()">+ ADD</span>
    </div>
    <div id="pipeline-list"></div>
  </div>
</div>

<script>
const BASE='http://127.0.0.1:8765';
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

// Clock
function tick(){const el=document.getElementById('clock');if(el)el.textContent=new Date().toLocaleTimeString('en-US',{hour12:false});}
tick(); setInterval(tick,1000);

// ── VOICE INDICATOR ───────────────────────────────────────────────────────────
async function pollVoice(){
  try{
    const r=await fetch(`${BASE}/api/voice/active`).then(r=>r.json());
    const pill=document.getElementById('voice-pill');
    if(pill) pill.style.display = r.agent==='gresz' ? 'flex' : 'none';
  }catch(_){}
}
pollVoice(); setInterval(pollVoice, 3000);

// Views
const VIEWS=['projects','clients','finance','reports'];
let _currentView='projects';
function showView(name){
  _currentView=name;
  VIEWS.forEach(v=>{ document.getElementById('view-'+v).style.display=v===name?'block':'none'; });
  document.querySelectorAll('.nav-link').forEach((el,i)=>{ el.classList.toggle('active',VIEWS[i]===name); });
}

// ── DATA ─────────────────────────────────────────────────────────────────────
let _projects=[], _clients=[], _pipeline=[];

async function loadAll(){
  try{
    const d=await fetch(`${BASE}/api/specialist/gresz/data`).then(r=>r.json());
    _projects=d.projects||[]; _clients=d.clients||[]; _pipeline=d.pipeline||[];
    renderKPIs(d.kpis||{});
    renderProjects(); renderClients(); renderPipeline();
  }catch(e){ console.error('Gresz load error',e); }
}

async function save(collection, data){
  await fetch(`${BASE}/api/specialist/gresz/save`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({collection,data})});
}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function renderKPIs(k){
  const s=id=>document.getElementById(id);
  s('kpi-pipe').textContent=k.pipeline_value||'$0';
  s('kpi-pipe-d').textContent=`${_pipeline.length} deals tracked`;
  s('kpi-clients').textContent=k.total_clients??'—';
  s('kpi-clients-d').textContent=`${_clients.filter(c=>c.tier==='PROSPECT').length} prospects`;
  s('kpi-tasks').textContent=k.active_projects??'—';
  s('kpi-tasks-d').textContent=k.overdue>0?`${k.overdue} overdue`:'All on track';
  s('kpi-tasks-d').className='kpi-delta '+(k.overdue>0?'down':'up');
  // Revenue KPI — sum closing deals
  const rev=_pipeline.filter(d=>d.stage==='closing').reduce((a,d)=>{
    const n=parseFloat(String(d.value||0).replace(/[$,]/g,'')||0);return a+n;},0);
  s('kpi-rev').textContent=rev>0?`$${(rev/1000).toFixed(1)}K`:'—';
  s('kpi-rev-d').textContent=`${_pipeline.filter(d=>d.stage==='closing').length} closing`;
}

// ── PROJECTS ─────────────────────────────────────────────────────────────────
function renderProjects(){
  const b=document.getElementById('proj-body');
  if(!_projects.length){ b.innerHTML='<tr><td colspan="5" style="color:var(--muted);text-align:center;padding:20px">No projects. Click + NEW PROJECT.</td></tr>'; return; }
  b.innerHTML=_projects.map((p,i)=>`
    <tr onclick="editProject(${i})" style="cursor:pointer">
      <td>${esc(p.name)}${p.overdue?'<span style="color:var(--red);font-size:9px;margin-left:6px">OVERDUE</span>':''}</td>
      <td style="color:var(--muted)">${esc(p.client||'—')}</td>
      <td><span class="proj-status ${p.status||'active'}">${(p.status||'active').toUpperCase()}</span></td>
      <td>
        <div class="progress-bar"><div class="progress-fill" style="width:${p.progress||0}%"></div></div>
        <div style="font-size:9px;color:var(--muted);margin-top:2px">${p.progress||0}%</div>
      </td>
      <td style="color:var(--muted)">${esc(p.due||'TBD')}</td>
    </tr>`).join('');
}

async function newProject(){
  const name=prompt('Project name:');if(!name)return;
  const client=prompt('Client:','Internal')||'Internal';
  const due=prompt('Due date (e.g. Jun 15):','TBD')||'TBD';
  _projects.unshift({id:Date.now(),name,client,status:'active',progress:0,due,notes:''});
  await save('projects',_projects); renderProjects(); renderKPIs({});
}

function editProject(i){
  const p=_projects[i];
  const prog=prompt(`Progress for "${p.name}" (0-100):`,p.progress??0);
  if(prog===null)return;
  const status=prompt('Status (active/hold/complete/urgent):',p.status||'active')||p.status;
  _projects[i].progress=Math.min(100,Math.max(0,parseInt(prog)||0));
  _projects[i].status=status;
  save('projects',_projects); renderProjects();
}

// ── CLIENTS ───────────────────────────────────────────────────────────────────
function renderClients(){
  const c=document.getElementById('clients-list');
  if(!_clients.length){ c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:12px">No clients yet.</div>'; return; }
  c.innerHTML=_clients.map((cl,i)=>`
    <div class="client-card">
      <div class="client-avatar">${esc((cl.avatar||cl.name?.[0]||'?').toUpperCase())}</div>
      <div style="flex:1">
        <div class="client-name">${esc(cl.name)}</div>
        <div class="client-tier">${esc(cl.tier||'PROSPECT')}</div>
      </div>
      <div class="client-value">${esc(cl.value||'—')}</div>
      <div onclick="deleteClient(${i})" style="color:var(--red);cursor:pointer;font-size:10px;margin-left:8px">✕</div>
    </div>`).join('');
}

async function newClient(){
  const name=prompt('Client name:');if(!name)return;
  const tier=prompt('Tier (PROSPECT/PROJECT/RETAINER):','PROSPECT')||'PROSPECT';
  const value=prompt('Value (e.g. $5,000/mo):','—')||'—';
  _clients.unshift({id:Date.now(),name,tier:tier.toUpperCase(),value,avatar:name[0].toUpperCase()});
  await save('clients',_clients); renderClients();
}

async function deleteClient(i){
  if(!confirm(`Remove "${_clients[i].name}"?`))return;
  _clients.splice(i,1); await save('clients',_clients); renderClients();
}

// ── PIPELINE ──────────────────────────────────────────────────────────────────
const STAGES=['lead','qualified','proposal','closing'];

function renderPipeline(){
  const c=document.getElementById('pipeline-list');
  if(!_pipeline.length){ c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:12px">No deals. Click + ADD.</div>'; return; }
  c.innerHTML=_pipeline.map((d,i)=>`
    <div class="pipe-card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div class="pipe-company">${esc(d.company)}</div>
        <div onclick="deleteDeal(${i})" style="color:var(--red);cursor:pointer;font-size:10px;margin-left:6px">✕</div>
      </div>
      <div class="pipe-value">${esc(d.value)}</div>
      <div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap">
        ${STAGES.map(s=>`<span onclick="setStage(${i},'${s}')"
          style="font-size:8px;padding:2px 6px;border-radius:2px;cursor:pointer;border:1px solid;
          ${d.stage===s?stageStyle(s):'border-color:var(--border);color:var(--muted)'}">
          ${s.toUpperCase()}</span>`).join('')}
      </div>
    </div>`).join('');
}

function stageStyle(s){
  const m={lead:'border-color:var(--muted);color:var(--muted)',qualified:'border-color:var(--blue);color:var(--blue)',
           proposal:'border-color:#ccaa44;color:#ccaa44',closing:'border-color:var(--green);color:var(--green)'};
  return m[s]||'border-color:var(--border);color:var(--muted)';
}

async function setStage(i,stage){
  _pipeline[i].stage=stage; await save('pipeline',_pipeline); renderPipeline(); renderKPIs({pipeline_value:'—'});
}

async function newDeal(){
  const company=prompt('Company name:');if(!company)return;
  const value=prompt('Deal value (e.g. $12,000):','$0')||'$0';
  _pipeline.unshift({id:Date.now(),company,value,stage:'lead'});
  await save('pipeline',_pipeline); renderPipeline(); renderKPIs({});
}

async function deleteDeal(i){
  if(!confirm(`Remove deal with "${_pipeline[i].company}"?`))return;
  _pipeline.splice(i,1); await save('pipeline',_pipeline); renderPipeline();
}

// ── REPORTS / BRIEFING ────────────────────────────────────────────────────────
async function loadReports(){
  const c=document.getElementById('view-reports');
  c.innerHTML='<div class="section-hdr"><h2>EXECUTIVE BRIEFING</h2></div><div style="color:var(--muted);font-size:12px;padding:20px">Generating AI briefing…</div>';
  try{
    const r=await fetch(`${BASE}/api/specialist/gresz/briefing`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json());
    c.innerHTML=`
      <div class="section-hdr"><h2>EXECUTIVE BRIEFING</h2></div>
      <div style="background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--gold);
        padding:16px;border-radius:4px;font-size:13px;line-height:1.8;white-space:pre-wrap">
        ${esc(r.briefing||'No briefing available.')}
      </div>`;
  }catch(e){
    c.innerHTML=`<div class="section-hdr"><h2>EXECUTIVE BRIEFING</h2></div><div style="color:var(--red);padding:20px;font-size:12px">Briefing unavailable: ${esc(String(e))}</div>`;
  }
}

// ── COMMAND ───────────────────────────────────────────────────────────────────
// ── MARKDOWN RENDERER ────────────────────────────────────────────────────────
function mdToHtml(t){
  t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/^### (.+)$/gm,'<div style="font-size:10px;letter-spacing:2px;color:var(--muted);margin:8px 0 3px;text-transform:uppercase">$1</div>');
  t=t.replace(/^## (.+)$/gm,'<div style="font-size:12px;color:var(--gold);letter-spacing:1px;margin:8px 0 4px">$1</div>');
  t=t.replace(/^# (.+)$/gm,'<div style="font-size:13px;font-weight:700;color:var(--gold);letter-spacing:2px;margin:8px 0 5px">$1</div>');
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
  const text=inp.value.trim();if(!text)return;inp.value='';
  const lower=text.toLowerCase();
  if(lower.includes('brief')||lower.includes('report')){ showView('reports'); loadReports(); return; }
  if(lower.includes('project')){ showView('projects'); return; }
  if(lower.includes('client')){ showView('clients'); return; }
  if(lower.includes('pipeline')||lower.includes('deal')){ /* stay */ return; }
  try{
    const r=await fetch(`${BASE}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:'[GRESZ] '+text})});
    const d=await r.json();
    const reply=d.response||d.message||'Done.';
    document.getElementById('view-'+_currentView).insertAdjacentHTML('afterbegin',
      `<div style="background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--gold);
        padding:12px;margin-bottom:12px;font-size:12px;border-radius:4px;line-height:1.6">${mdToHtml(reply)}</div>`);
  }catch(e){console.error(e);}
}

// Override showView to lazy-load reports
const _origShowView=showView;
function showView(name){
  _origShowView(name);
  if(name==='reports') loadReports();
}

// ── INIT ──────────────────────────────────────────────────────────────────────
loadAll();
setInterval(loadAll, 5*60*1000);
</script>
</body>
</html>"""
