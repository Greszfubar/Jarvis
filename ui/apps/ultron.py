"""ULTRON — Security specialist app HTML shell."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ULTRON — GreszTech</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:    #070707;
  --bg1:   #0e0e0e;
  --bg2:   #141414;
  --panel: #111;
  --red:   #cc0000;
  --red2:  #ff2222;
  --redlo: rgba(204,0,0,.12);
  --border:#2a0a0a;
  --text:  #d0c8c8;
  --muted: #5a4040;
  --green: #00cc44;
  --yellow:#ccaa00;
  --blue:  #0066cc;
  --grey:  #444;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Courier New',monospace;overflow:hidden}
/* ── TOP BAR ── */
#topbar{height:48px;display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;border-bottom:1px solid var(--border);background:var(--bg1);flex-shrink:0}
.tb-brand{display:flex;align-items:baseline;gap:12px}
.tb-name{font-size:22px;font-weight:900;letter-spacing:8px;color:var(--red);
  text-shadow:0 0 20px rgba(204,0,0,.6)}
.tb-sub{font-size:9px;letter-spacing:4px;color:var(--muted)}
.tb-right{display:flex;align-items:center;gap:16px}
.tb-status{font-size:9px;letter-spacing:3px;display:flex;align-items:center;gap:6px}
.status-dot{width:7px;height:7px;border-radius:50%;animation:pulse-r 2s infinite}
.status-dot.online{background:var(--red);box-shadow:0 0 8px var(--red)}
@keyframes pulse-r{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes vpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.4)}}
/* ── LAYOUT ── */
#app{display:flex;flex-direction:column;height:100vh}
#body{display:flex;flex:1;overflow:hidden}
/* ── TOOL HEALTH GRID ── */
#health-bar{height:72px;border-bottom:1px solid var(--border);background:var(--bg1);
  display:flex;align-items:center;padding:0 20px;gap:10px;flex-shrink:0;overflow-x:auto}
.th-card{flex-shrink:0;background:var(--bg2);border:1px solid var(--border);border-radius:3px;
  padding:8px 14px;display:flex;flex-direction:column;align-items:center;gap:4px;min-width:100px;cursor:default}
.th-card:hover{border-color:var(--muted)}
.th-label{font-size:8px;letter-spacing:2px;color:var(--muted)}
.th-dot{width:10px;height:10px;border-radius:50%}
.th-dot.green{background:var(--green);box-shadow:0 0 8px var(--green)}
.th-dot.yellow{background:var(--yellow);box-shadow:0 0 8px var(--yellow)}
.th-dot.red{background:var(--red);box-shadow:0 0 8px var(--red)}
.th-dot.grey{background:var(--grey)}
.th-state{font-size:8px;color:var(--muted);letter-spacing:1px}
/* ── LEFT — EXPOSURE LOG ── */
#log-panel{width:55%;border-right:1px solid var(--border);display:flex;flex-direction:column}
.panel-head{padding:12px 16px;border-bottom:1px solid var(--border);background:var(--bg1);
  font-size:9px;letter-spacing:3px;color:var(--muted);flex-shrink:0;display:flex;justify-content:space-between;align-items:center}
#log-list{flex:1;overflow-y:auto;padding:12px}
#log-list::-webkit-scrollbar{width:3px}
#log-list::-webkit-scrollbar-thumb{background:var(--border)}
.log-entry{border:1px solid var(--border);border-radius:2px;padding:10px 14px;
  margin-bottom:8px;border-left:3px solid var(--border);transition:background .15s;cursor:default}
.log-entry:hover{background:var(--bg2)}
.log-entry.info{border-left-color:var(--blue)}
.log-entry.watch{border-left-color:var(--yellow);cursor:pointer}
.log-entry.alert{border-left-color:var(--red);background:rgba(204,0,0,.05)}
.log-entry.resolved{border-left-color:var(--green);opacity:.6}
.log-title{font-size:10px;color:var(--text);margin-bottom:4px}
.log-detail{font-size:9px;color:var(--muted);margin-bottom:6px}
.log-meta{display:flex;gap:8px;align-items:center}
.log-badge{font-size:8px;padding:2px 6px;border-radius:1px;letter-spacing:1px}
.badge-info{background:rgba(0,102,204,.15);color:#4499ff;border:1px solid #004488}
.badge-watch{background:rgba(204,170,0,.12);color:var(--yellow);border:1px solid var(--yellow)}
.badge-alert{background:var(--redlo);color:var(--red2);border:1px solid var(--red)}
.badge-resolved{background:rgba(0,204,68,.1);color:var(--green);border:1px solid var(--green)}
.badge-resolving{background:rgba(0,104,204,.1);color:#66aaff;border:1px solid #0055aa}
.log-progress{height:2px;background:var(--border);border-radius:1px;margin-top:6px;overflow:hidden}
.log-progress-fill{height:100%;background:var(--blue);border-radius:1px;transition:width .5s}
.log-ts{font-size:8px;color:var(--muted)}
/* ── RIGHT ── */
#right-panel{flex:1;display:flex;flex-direction:column}
/* Threat scanner */
#scanner-section{flex:1;border-bottom:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}
.scanner-body{padding:14px;flex:1;overflow-y:auto}
.scan-input-row{display:flex;gap:8px;margin-bottom:14px}
.scan-input{flex:1;background:var(--bg2);border:1px solid var(--border);color:var(--text);
  padding:9px 14px;font-family:inherit;font-size:11px;outline:none;border-radius:2px}
.scan-input:focus{border-color:var(--red)}
.scan-btn{background:var(--redlo);border:1px solid var(--red);color:var(--red);
  padding:9px 18px;font-family:inherit;font-size:9px;letter-spacing:2px;cursor:pointer;border-radius:2px}
.scan-btn:hover{background:rgba(204,0,0,.2)}
.watchlist-item{display:flex;justify-content:space-between;align-items:center;
  padding:8px 12px;border:1px solid var(--border);border-radius:2px;margin-bottom:6px;font-size:10px}
.watchlist-domain{color:var(--text)}
.watchlist-scan{font-size:8px;color:var(--muted);cursor:pointer;border:1px solid var(--border);
  padding:2px 8px;border-radius:1px}
.watchlist-scan:hover{border-color:var(--red);color:var(--red)}
#scan-result{background:var(--bg2);border:1px solid var(--border);border-radius:2px;
  padding:12px;font-size:10px;line-height:1.6;display:none;margin-bottom:12px}
/* Tool vault */
#vault-section{flex:1;display:flex;flex-direction:column;overflow:hidden}
.vault-body{padding:14px;flex:1;overflow-y:auto}
.vault-body::-webkit-scrollbar{width:3px}
.vault-body::-webkit-scrollbar-thumb{background:var(--border)}
.vault-item{display:flex;align-items:center;gap:10px;padding:9px 12px;
  border:1px solid var(--border);border-radius:2px;margin-bottom:6px;cursor:pointer;transition:background .15s}
.vault-item:hover{background:var(--bg2);border-color:var(--muted)}
.vault-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.vault-name{font-size:10px;flex:1}
.vault-desc{font-size:9px;color:var(--muted)}
.vault-status{font-size:8px;letter-spacing:1px}
/* misc */
.empty{color:var(--muted);font-size:10px;padding:20px;text-align:center}
.section-label{font-size:8px;letter-spacing:3px;color:var(--muted);margin-bottom:10px}
</style>
</head>
<body>
<div id="app">

  <!-- TOP BAR -->
  <div id="topbar">
    <div class="tb-brand">
      <div class="tb-name">ULTRON</div>
      <div class="tb-sub">GRESZTECH · SECURITY DIVISION</div>
    </div>
    <div class="tb-right">
      <div id="voice-pill" style="display:none;align-items:center;gap:6px;background:rgba(220,38,38,.15);border:1px solid rgba(220,38,38,.4);border-radius:20px;padding:3px 10px;font-size:9px;letter-spacing:1px;color:#f87171">
        <span id="voice-dot" style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#f87171;animation:vpulse 1.2s ease-in-out infinite"></span>
        VOICE ACTIVE
      </div>
      <div class="tb-status">
        <div class="status-dot online"></div>
        <span style="color:var(--red);letter-spacing:2px;font-size:9px">MONITORING</span>
      </div>
      <div id="tb-scan-time" style="font-size:8px;color:var(--muted)">Last scan: —</div>
      <div id="clock" style="font-size:10px;color:var(--muted);font-family:'Courier New',monospace;min-width:60px;text-align:right"></div>
    </div>
  </div>

  <!-- TOOL HEALTH GRID -->
  <div id="health-bar">
    <div style="font-size:8px;letter-spacing:2px;color:var(--muted);margin-right:8px;flex-shrink:0">SYSTEMS</div>
    <div id="health-cards">
      <!-- populated by JS -->
    </div>
  </div>

  <!-- BODY -->
  <div id="body">

    <!-- LEFT — EXPOSURE LOG -->
    <div id="log-panel">
      <div class="panel-head">
        <span>EXPOSURE LOG</span>
        <span id="log-alert-count" style="color:var(--red)"></span>
      </div>
      <div id="log-list">
        <div class="empty">Initializing security monitor…</div>
      </div>
    </div>

    <!-- RIGHT -->
    <div id="right-panel">

      <!-- THREAT SCANNER -->
      <div id="scanner-section">
        <div class="panel-head">THREAT SCANNER</div>
        <div class="scanner-body">
          <div class="section-label">SCAN DOMAIN / IP</div>
          <div class="scan-input-row">
            <input class="scan-input" id="scan-input" placeholder="domain.com or 192.168.x.x"
                   onkeydown="if(event.key==='Enter') runScan()"/>
            <button class="scan-btn" onclick="runScan()">SCAN</button>
            <button class="scan-btn" onclick="addToWatchlist()" title="Add to watchlist"
              style="padding:0 10px">+</button>
          </div>
          <div style="display:flex;gap:6px;margin-bottom:10px">
            <button onclick="runBreachCheck()"
              style="background:transparent;border:1px solid var(--border);color:var(--muted);
              padding:5px 10px;cursor:pointer;font-family:inherit;font-size:9px;letter-spacing:1px;
              border-radius:2px;transition:all .2s"
              onmouseover="this.style.borderColor='var(--red)';this.style.color='var(--red)'"
              onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--muted)'">
              ✉ CHECK EMAIL BREACH
            </button>
          </div>
          <div id="scan-result"></div>
          <div class="section-label">WATCHLIST</div>
          <div id="watchlist"></div>
        </div>
      </div>

      <!-- TOOL VAULT -->
      <div id="vault-section">
        <div class="panel-head">TOOL VAULT · API KEYS & CONFIG</div>
        <div class="vault-body" id="vault-body">
          <div class="empty">Loading vault…</div>
        </div>
      </div>

    </div>
  </div>

</div>
<script>
const BASE = 'http://127.0.0.1:8765';

// ── UTILS ─────────────────────────────────────────────────────────────────────
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── CLOCK ─────────────────────────────────────────────────────────────────────
function tick(){ const el=document.getElementById('clock'); if(el) el.textContent=new Date().toLocaleTimeString('en-US',{hour12:false}); }
tick(); setInterval(tick, 1000);

// ── VOICE INDICATOR ───────────────────────────────────────────────────────────
async function pollVoice(){
  try{
    const r=await fetch(`${BASE}/api/voice/active`).then(r=>r.json());
    const pill=document.getElementById('voice-pill');
    if(pill) pill.style.display = r.agent==='ultron' ? 'flex' : 'none';
  }catch(_){}
}
pollVoice(); setInterval(pollVoice, 3000);

// ── TOOL HEALTH ───────────────────────────────────────────────────────────────
const HEALTH_ITEMS = [
  {label:'CLAUDE AI',     key:'ANTHROPIC_API_KEY'},
  {label:'TELEGRAM',      key:'TELEGRAM_BOT_TOKEN'},
  {label:'NEWSAPI',       key:'NEWSAPI_KEY'},
  {label:'ELEVENLABS',    key:'ELEVENLABS_API_KEY'},
  {label:'GMAIL OAUTH',   key:'GOOGLE_CLIENT_ID'},
  {label:'WEATHER',       key:'WEATHER_CITY', alwaysOk:true},
  {label:'HIBP',          key:'HIBP_API_KEY'},
];

let _vaultPw = '';
let _vaultTools = [];

async function loadVault(pw){
  const r = await fetch(`${BASE}/api/tools?password=${encodeURIComponent(pw)}`).then(r=>r.json());
  if(r.error) return false;
  _vaultPw = pw;
  _vaultTools = r.tools||[];
  renderHealth();
  renderVault();
  return true;
}

function renderHealth(){
  const el = document.getElementById('health-cards');
  el.innerHTML = HEALTH_ITEMS.map(h=>{
    const tool = _vaultTools.find(t=>t.key===h.key);
    const cfg  = h.alwaysOk || (tool && tool.configured);
    return `<div class="th-card" title="${h.key}">
      <div class="th-dot ${cfg?'green':'grey'}"></div>
      <div class="th-label">${h.label}</div>
      <div class="th-state" style="color:${cfg?'var(--green)':'var(--muted)'}">${cfg?'ACTIVE':'NOT SET'}</div>
    </div>`;
  }).join('');
  document.getElementById('tb-scan-time').textContent = 'Refreshed: ' + new Date().toLocaleTimeString();
}

// ── VAULT ─────────────────────────────────────────────────────────────────────
function renderVault(){
  if(!_vaultPw){
    document.getElementById('vault-body').innerHTML = `
      <div class="section-label">AUTHENTICATION REQUIRED</div>
      <div style="display:flex;gap:8px;margin-bottom:12px">
        <input type="password" id="vault-pw" placeholder="Enter password…"
          style="flex:1;background:var(--bg2);border:1px solid var(--border);color:var(--text);
          padding:9px 14px;font-family:inherit;font-size:12px;letter-spacing:2px;outline:none;border-radius:2px"
          onkeydown="if(event.key==='Enter') unlockVault()"/>
        <button class="scan-btn" onclick="unlockVault()">UNLOCK</button>
      </div>
      <div id="vault-err" style="font-size:9px;color:var(--red);display:none">INCORRECT PASSWORD</div>`;
    setTimeout(()=>document.getElementById('vault-pw')?.focus(), 50);
    return;
  }
  document.getElementById('vault-body').innerHTML = `
    <div style="font-size:9px;color:var(--green);letter-spacing:2px;margin-bottom:12px">
      🔓 VAULT UNLOCKED · ${_vaultTools.filter(t=>t.configured).length}/${_vaultTools.length} CONFIGURED
    </div>
    ${_vaultTools.map((t,i)=>`
      <div id="vi-${i}">
        <div class="vault-item" onclick="toggleVaultEdit(${i})">
          <div class="vault-dot" style="background:${t.configured?'var(--green)':'var(--grey)'}"></div>
          <div style="flex:1;min-width:0">
            <div class="vault-name">${esc(t.name)}</div>
            <div class="vault-desc">${esc(t.desc)}</div>
          </div>
          <div class="vault-status" style="color:${t.configured?'var(--green)':'var(--muted)'}">
            ${t.configured?esc(t.masked):'NOT SET'}
          </div>
        </div>
        <div id="ve-${i}" style="display:none;padding:12px 14px;background:var(--bg2);
          border:1px solid var(--border);border-top:none;margin-bottom:6px">
          <div style="font-size:8px;color:var(--muted);margin-bottom:6px;letter-spacing:2px">${esc(t.key)}</div>
          <input type="${t.key.includes('KEY')||t.key.includes('TOKEN')?'password':'text'}"
            id="vv-${i}" value="${esc(t.value)}" placeholder="Enter value…"
            style="width:100%;background:var(--bg1);border:1px solid var(--border);color:var(--text);
            padding:8px 12px;font-family:monospace;font-size:12px;outline:none;border-radius:2px;margin-bottom:8px"
            onkeydown="if(event.key==='Enter') saveVaultEdit(${i},'${esc(t.key)}')"/>
          <div style="display:flex;gap:8px">
            <button class="scan-btn" onclick="saveVaultEdit(${i},'${esc(t.key)}')">SAVE</button>
            ${t.docs?`<a href="${esc(t.docs)}" target="_blank" class="scan-btn" style="text-decoration:none">DOCS ↗</a>`:''}
            <button class="scan-btn" style="border-color:var(--muted);color:var(--muted)" onclick="toggleVaultEdit(${i})">CANCEL</button>
          </div>
        </div>
      </div>`).join('')}`;
}
async function unlockVault(){
  const pw = document.getElementById('vault-pw')?.value||'';
  const ok = await loadVault(pw);
  if(!ok){ document.getElementById('vault-err').style.display=''; }
}
function toggleVaultEdit(i){
  const el=document.getElementById('ve-'+i);
  if(el){ el.style.display=el.style.display==='none'?'':'none'; }
  if(el&&el.style.display!=='none') document.getElementById('vv-'+i)?.focus();
}
async function saveVaultEdit(i, key){
  const val = document.getElementById('vv-'+i)?.value||'';
  const r = await fetch(`${BASE}/api/tools`,{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({password:_vaultPw,key,value:val})}).then(r=>r.json());
  if(r.error){alert('Error: '+r.error);return;}
  await loadVault(_vaultPw);
}

// ── EXPOSURE LOG ─────────────────────────────────────────────────────────────
async function loadLogs(){
  try{
    const r = await fetch(`${BASE}/api/specialist/ultron/logs`).then(r=>r.json());
    const logs = r.logs||[];
    const el = document.getElementById('log-list');
    const alerts = logs.filter(l=>l.severity==='alert'&&l.status==='open').length;
    const ac = document.getElementById('log-alert-count');
    ac.textContent = alerts>0 ? `${alerts} ALERT${alerts>1?'S':''}` : '';
    if(!logs.length){ el.innerHTML='<div class="empty">No security events logged</div>'; return; }
    el.innerHTML = logs.map(l=>{
      const sev = l.severity||'info';
      const status = l.status||'open';
      let badge, badgeCls;
      if(status==='resolved'){    badge='RESOLVED'; badgeCls='badge-resolved'; }
      else if(status==='resolving'){ badge=`RESOLVING ${l.progress||0}%`; badgeCls='badge-resolving'; }
      else if(sev==='alert'){     badge='EXPOSED';  badgeCls='badge-alert'; }
      else if(sev==='watch'){     badge='REVIEW';   badgeCls='badge-watch'; }
      else {                      badge='INFO';      badgeCls='badge-info'; }
      const progress = (status==='resolving')
        ? `<div class="log-progress"><div class="log-progress-fill" style="width:${l.progress||0}%"></div></div>` : '';
      return `<div class="log-entry ${sev}">
        <div class="log-title">${esc(l.title)}</div>
        ${l.detail?`<div class="log-detail">${esc(l.detail)}</div>`:''}
        <div class="log-meta">
          <span class="log-badge ${badgeCls}">${badge}</span>
          <span class="log-ts">${(l.ts||'').slice(0,16).replace('T',' ')}</span>
        </div>
        ${progress}
      </div>`;
    }).join('');
  }catch(e){}
}

// ── THREAT SCANNER ────────────────────────────────────────────────────────────
let _scanActive = false;

async function runScan(domain){
  domain = domain || document.getElementById('scan-input').value.trim();
  if(!domain || _scanActive) return;
  _scanActive = true;
  const el = document.getElementById('scan-result');
  el.style.display='block';
  el.innerHTML=`<span style="color:var(--muted)">▶ Scanning ${esc(domain)}…</span>`;
  try{
    const r = await fetch(`${BASE}/api/specialist/ultron/scan?target=${encodeURIComponent(domain)}`).then(r=>r.json());
    if(r.error){ el.innerHTML=`<span style="color:var(--red)">✗ ${esc(r.error)}</span>`; _scanActive=false; return; }

    const safe = r.safe !== false;
    const risk = r.risk || (safe ? 'clean' : 'medium');
    const riskCol = {clean:'var(--green)',medium:'var(--yellow)',high:'var(--red)'}[risk]||'var(--muted)';

    const geo = r.checks?.geo||{};
    const ssl = r.checks?.ssl||{};
    const dns = r.checks?.dns||{};
    const dnsbl = r.checks?.dnsbl||{};

    const threats = r.threats||[];
    const threatHtml = threats.length
      ? `<div style="margin-top:8px;padding:8px;background:rgba(204,0,0,.08);border:1px solid var(--red);border-radius:2px">
          ${threats.map(t=>`<div style="font-size:10px;color:var(--red)">⚠ ${esc(t)}</div>`).join('')}
         </div>`
      : '';

    const sslHtml = ssl.valid===true
      ? `<span style="color:var(--green)">✓ Valid (${ssl.issuer||'?'}${ssl.days_left!=null?`, ${ssl.days_left}d left`:''})</span>`
      : ssl.valid===false
        ? `<span style="color:var(--red)">✗ Invalid: ${esc(ssl.error||'')}</span>`
        : `<span style="color:var(--muted)">N/A</span>`;

    el.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">
        <div style="font-size:13px;color:${riskCol};font-weight:700">
          ${safe?'✓ CLEAN':'⚠ THREATS DETECTED'}
        </div>
        <div style="font-size:9px;padding:2px 8px;border:1px solid ${riskCol};color:${riskCol};border-radius:2px">
          ${risk.toUpperCase()}
        </div>
        <button onclick="addToWatchlist('${esc(domain)}')"
          style="margin-left:auto;background:transparent;border:1px solid var(--border);
          color:var(--muted);padding:3px 8px;cursor:pointer;font-family:inherit;font-size:9px;border-radius:2px"
          onmouseover="this.style.borderColor='var(--red)';this.style.color='var(--red)'"
          onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--muted)'">
          + WATCHLIST
        </button>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10px;color:var(--muted);line-height:2">
        <div>IP: <span style="color:var(--text)">${esc(r.ip||'?')}</span></div>
        <div>TYPE: <span style="color:var(--text)">${esc(r.kind||'?').toUpperCase()}</span></div>
        <div>COUNTRY: <span style="color:var(--text)">${esc(geo.country||'?')} ${esc(geo.city||'')}</span></div>
        <div>ORG: <span style="color:var(--text)">${esc((geo.org||'?').slice(0,28))}</span></div>
        <div>DNSBL: <span style="color:${dnsbl.hit?'var(--red)':'var(--green)'}">${dnsbl.hit?'BLACKLISTED ('+dnsbl.lists?.join(', ')+')':'CLEAN'}</span></div>
        <div>SSL: ${sslHtml}</div>
        ${dns.A?.length?`<div style="grid-column:1/-1">DNS A: <span style="color:var(--text)">${dns.A.slice(0,3).map(esc).join(', ')}</span></div>`:''}
      </div>
      ${threatHtml}`;
    if(!safe) loadLogs();
  }catch(e){
    el.innerHTML=`<span style="color:var(--muted)">Scan error: ${esc(String(e))}</span>`;
  }
  _scanActive=false;
}

// ── BREACH CHECK ─────────────────────────────────────────────────────────────
async function runBreachCheck(){
  const email = prompt('Enter email to check for breaches:');
  if(!email||!email.includes('@')) return;
  const el = document.getElementById('scan-result');
  el.style.display='block';
  el.innerHTML=`<span style="color:var(--muted)">Checking ${esc(email)} against HaveIBeenPwned…</span>`;
  try{
    const r = await fetch(`${BASE}/api/specialist/ultron/breach?email=${encodeURIComponent(email)}`).then(r=>r.json());
    if(r.error){
      el.innerHTML=`<div style="color:var(--muted)">${esc(r.error)}<br><span style="font-size:9px">Add HIBP_API_KEY in Tool Vault to enable breach checking.</span></div>`;
      return;
    }
    if(!r.pwned){
      el.innerHTML=`<div style="color:var(--green)">✓ ${esc(email)} — not found in any known breaches.</div>`;
      return;
    }
    el.innerHTML = `
      <div style="color:var(--red);margin-bottom:8px">⚠ ${esc(email)} found in ${r.breaches.length} breach${r.breaches.length>1?'es':''}:</div>
      ${r.breaches.map(b=>`
        <div style="background:rgba(204,0,0,.08);border:1px solid var(--border);border-radius:2px;
          padding:8px 10px;margin-bottom:4px;font-size:10px">
          <span style="color:var(--text)">${esc(b.name)}</span>
          <span style="color:var(--muted);margin-left:8px">${esc(b.date||'')} · ${b.count?.toLocaleString()||'?'} records</span>
        </div>`).join('')}`;
  }catch(e){ el.innerHTML=`<span style="color:var(--muted)">Breach check failed: ${esc(String(e))}</span>`; }
}

// ── WATCHLIST ─────────────────────────────────────────────────────────────────
async function loadWatchlist(){
  try{
    const r = await fetch(`${BASE}/api/specialist/ultron/watchlist`).then(r=>r.json());
    const wl = r.watchlist||[];
    const el = document.getElementById('watchlist');
    if(!wl.length){ el.innerHTML='<div style="font-size:10px;color:var(--muted);padding:4px 0">No targets — enter a domain above.</div>'; return; }
    el.innerHTML = wl.map(d=>`
      <div class="watchlist-item">
        <span class="watchlist-domain">${esc(d)}</span>
        <div style="display:flex;gap:6px">
          <span class="watchlist-scan" onclick="runScan('${esc(d)}')">SCAN</span>
          <span class="watchlist-scan" style="border-color:var(--muted);color:var(--muted)"
            onclick="removeFromWatchlist('${esc(d)}')">✕</span>
        </div>
      </div>`).join('');
  }catch(e){}
}

async function addToWatchlist(domain){
  domain = domain || document.getElementById('scan-input').value.trim();
  if(!domain) return;
  await fetch(`${BASE}/api/specialist/ultron/watchlist`,{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:'add',target:domain})});
  loadWatchlist();
}

async function removeFromWatchlist(domain){
  await fetch(`${BASE}/api/specialist/ultron/watchlist`,{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:'remove',target:domain})});
  loadWatchlist();
}

// ── INIT ──────────────────────────────────────────────────────────────────────
renderVault();
loadWatchlist();
loadLogs();
setInterval(loadLogs, 30000);
setInterval(loadWatchlist, 60000);
</script>
</body>
</html>"""
