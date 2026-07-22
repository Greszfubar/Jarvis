"""VISION — Intelligence & Planning specialist app HTML shell."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VISION — GreszTech</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:    #071a0f;
  --bg1:   #0c2418;
  --bg2:   #112e1e;
  --panel: #0e2419;
  --green: #00cc66;
  --green2:#00ff88;
  --glo:   rgba(0,204,102,.12);
  --border:#0a3020;
  --text:  #c0d8c8;
  --muted: #3a6050;
  --red:   #cc4444;
  --yellow:#ccaa00;
  --blue:  #2288cc;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Courier New',monospace;overflow:hidden}
#topbar{height:48px;display:flex;align-items:center;justify-content:space-between;
  padding:0 24px;border-bottom:1px solid var(--border);background:var(--bg1);flex-shrink:0}
#topbar .logo{font-size:18px;font-weight:700;letter-spacing:4px;color:var(--green);text-shadow:0 0 12px var(--green)}
#topbar .subtitle{font-size:10px;color:var(--muted);letter-spacing:2px}
#topbar .status-row{display:flex;gap:12px;align-items:center}
.status-pill{font-size:10px;padding:3px 10px;border-radius:3px;border:1px solid;letter-spacing:1px}
.status-pill.online{border-color:var(--green);color:var(--green);background:var(--glo)}
.status-pill.offline{border-color:#555;color:#555}

#layout{display:flex;height:calc(100% - 48px);overflow:hidden}

/* ── LEFT: Plans & Strategy ── */
#left{width:340px;flex-shrink:0;border-right:1px solid var(--border);
  display:flex;flex-direction:column;background:var(--bg1)}
.panel-header{padding:12px 16px;font-size:10px;letter-spacing:2px;color:var(--muted);
  border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.panel-header span{color:var(--green);font-size:9px;cursor:pointer}
.panel-header span:hover{text-shadow:0 0 6px var(--green)}

#plans-list{flex:1;overflow-y:auto;padding:8px}
.plan-card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;
  padding:12px;margin-bottom:8px;cursor:pointer;transition:border-color .2s}
.plan-card:hover{border-color:var(--green)}
.plan-card.active{border-color:var(--green);background:var(--glo)}
.plan-title{font-size:13px;color:var(--text);margin-bottom:4px}
.plan-meta{font-size:10px;color:var(--muted);display:flex;gap:8px}
.plan-phase{font-size:9px;padding:2px 6px;border-radius:2px;border:1px solid var(--green);color:var(--green)}
.plan-due{font-size:9px;color:var(--yellow)}

#new-plan-btn{margin:8px;padding:10px;background:transparent;border:1px dashed var(--border);
  color:var(--muted);cursor:pointer;border-radius:4px;font-family:inherit;font-size:11px;
  letter-spacing:1px;transition:all .2s;text-align:center}
#new-plan-btn:hover{border-color:var(--green);color:var(--green)}

/* ── CENTER: Events Timeline ── */
#center{flex:1;display:flex;flex-direction:column;background:var(--bg)}

#timeline-wrap{flex:1;overflow-y:auto;padding:16px}
.timeline-day{margin-bottom:24px}
.day-label{font-size:10px;color:var(--green);letter-spacing:2px;margin-bottom:8px;
  padding-bottom:4px;border-bottom:1px solid var(--border)}
.event-row{display:flex;gap:12px;margin-bottom:8px;align-items:flex-start}
.event-time{font-size:10px;color:var(--muted);width:48px;flex-shrink:0;padding-top:2px}
.event-bar{width:3px;flex-shrink:0;border-radius:2px;align-self:stretch;min-height:40px}
.event-bar.work{background:var(--blue)}
.event-bar.personal{background:var(--green)}
.event-bar.deadline{background:var(--red)}
.event-bar.meeting{background:var(--yellow)}
.event-card{flex:1;background:var(--bg2);border:1px solid var(--border);
  border-radius:4px;padding:10px 12px}
.event-title{font-size:13px;color:var(--text);margin-bottom:2px}
.event-detail{font-size:10px;color:var(--muted)}
.event-tag{display:inline-block;font-size:9px;padding:1px 6px;border-radius:2px;
  margin-top:4px;border:1px solid;letter-spacing:1px}
.event-tag.work{border-color:var(--blue);color:var(--blue)}
.event-tag.personal{border-color:var(--green);color:var(--green)}
.event-tag.deadline{border-color:var(--red);color:var(--red)}

/* ── RIGHT: Calendar ── */
#right{width:300px;flex-shrink:0;border-left:1px solid var(--border);
  display:flex;flex-direction:column;background:var(--bg1)}
#cal-wrap{padding:16px}
#cal-nav{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
#cal-month{font-size:13px;color:var(--green);letter-spacing:2px}
.cal-nav-btn{background:transparent;border:1px solid var(--border);color:var(--muted);
  cursor:pointer;padding:4px 8px;border-radius:3px;font-size:12px}
.cal-nav-btn:hover{border-color:var(--green);color:var(--green)}
#cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}
.cal-dow{font-size:9px;color:var(--muted);text-align:center;padding:4px 0;letter-spacing:1px}
.cal-day{font-size:11px;text-align:center;padding:6px 2px;border-radius:3px;cursor:pointer;
  color:var(--muted);transition:all .15s}
.cal-day:hover{background:var(--bg2);color:var(--text)}
.cal-day.today{background:var(--glo);color:var(--green);border:1px solid var(--green)}
.cal-day.has-event::after{content:'·';color:var(--green);display:block;font-size:16px;line-height:0;margin-top:2px}
.cal-day.empty{pointer-events:none}

#mini-agenda{flex:1;overflow-y:auto;border-top:1px solid var(--border);padding:12px}
.agenda-item{padding:8px 10px;margin-bottom:6px;background:var(--bg2);
  border-left:3px solid var(--green);border-radius:0 4px 4px 0}
.agenda-time{font-size:10px;color:var(--muted)}
.agenda-title{font-size:12px;color:var(--text)}

/* ── BOTTOM: Command Bar ── */
#cmd-bar{height:50px;border-top:1px solid var(--border);background:var(--bg1);
  display:flex;align-items:center;padding:0 16px;gap:12px}
#cmd-input{flex:1;background:transparent;border:1px solid var(--border);
  color:var(--text);padding:8px 12px;font-family:inherit;font-size:13px;
  border-radius:4px;outline:none}
#cmd-input:focus{border-color:var(--green)}
#cmd-input::placeholder{color:var(--muted)}
#cmd-send{background:var(--green);color:#000;border:none;padding:8px 16px;
  border-radius:4px;cursor:pointer;font-family:inherit;font-size:12px;font-weight:700;
  letter-spacing:1px}
#cmd-send:hover{background:var(--green2)}

/* scrollbar */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
@keyframes vpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(1.4)}}
</style>
</head>
<body>
<div id="topbar">
  <div>
    <div class="logo">⬡ VISION</div>
    <div class="subtitle">INTELLIGENCE &amp; PLANNING — GRESZTECH LAYER 2</div>
  </div>
  <div class="status-row">
    <div id="voice-pill" style="display:none;align-items:center;gap:6px;background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.4);border-radius:20px;padding:3px 10px;font-size:9px;letter-spacing:1px;color:#4ade80">
      <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#4ade80;animation:vpulse 1.2s ease-in-out infinite"></span>
      VOICE ACTIVE
    </div>
    <div class="status-pill online" id="agent-status">● ONLINE</div>
    <div class="status-pill offline" id="cal-status">◌ CALENDAR</div>
    <div style="font-size:10px;color:var(--muted)" id="clock"></div>
  </div>
</div>

<div id="layout">
  <!-- LEFT: Plans -->
  <div id="left">
    <div class="panel-header">
      STRATEGIC PLANS
      <span style="display:flex;gap:12px;align-items:center">
        <span onclick="refreshPlans()" style="opacity:.6;font-size:10px">↻</span>
        <span onclick="newPlan()">+ NEW</span>
      </span>
    </div>
    <div id="plans-list"></div>
    <button id="new-plan-btn" onclick="newPlan()">+ CREATE NEW PLAN</button>
  </div>

  <!-- CENTER: Timeline -->
  <div id="center">
    <div class="panel-header" style="border-top:none">
      EVENTS TIMELINE
      <span onclick="loadTimeline()">↻ REFRESH</span>
    </div>
    <div id="timeline-wrap">
      <div style="text-align:center;color:var(--muted);padding:60px;font-size:12px">
        Loading events…
      </div>
    </div>
    <div id="cmd-bar">
      <input id="cmd-input" placeholder="Ask VISION to plan, schedule, research…" onkeydown="cmdKey(event)">
      <button id="cmd-send" onclick="sendCmd()">SEND</button>
    </div>
  </div>

  <!-- RIGHT: Calendar -->
  <div id="right">
    <div class="panel-header">CALENDAR</div>
    <div id="cal-wrap">
      <div id="cal-nav">
        <button class="cal-nav-btn" onclick="calShift(-1)">&#8249;</button>
        <div id="cal-month"></div>
        <button class="cal-nav-btn" onclick="calShift(1)">&#8250;</button>
      </div>
      <div id="cal-grid"></div>
    </div>
    <div class="panel-header" style="border-top:1px solid var(--border)">
      AGENDA
    </div>
    <div id="mini-agenda"></div>
  </div>
</div>

<script>
const BASE = 'http://127.0.0.1:8765';
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

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
    if(pill) pill.style.display = r.agent==='vision' ? 'flex' : 'none';
  }catch(_){}
}
pollVoice(); setInterval(pollVoice, 3000);

// ── CALENDAR WIDGET ────────────────────────────────────────────────────────────
let calYear=new Date().getFullYear(), calMonth=new Date().getMonth();
let _eventDates=new Set();
const DAYS=['SUN','MON','TUE','WED','THU','FRI','SAT'];
const MONTHS=['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE',
              'JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];

function renderCal(){
  document.getElementById('cal-month').textContent=`${MONTHS[calMonth]} ${calYear}`;
  const grid=document.getElementById('cal-grid');
  grid.innerHTML='';
  DAYS.forEach(d=>{
    const el=document.createElement('div');el.className='cal-dow';el.textContent=d;grid.appendChild(el);
  });
  const first=new Date(calYear,calMonth,1).getDay();
  const days=new Date(calYear,calMonth+1,0).getDate();
  const today=new Date();
  for(let i=0;i<first;i++){
    const el=document.createElement('div');el.className='cal-day empty';grid.appendChild(el);
  }
  for(let d=1;d<=days;d++){
    const el=document.createElement('div');el.className='cal-day';el.textContent=d;
    if(d===today.getDate()&&calMonth===today.getMonth()&&calYear===today.getFullYear())
      el.classList.add('today');
    // Mark days that have events
    const key=`${calYear}-${String(calMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    if(_eventDates.has(key)) el.classList.add('has-event');
    grid.appendChild(el);
  }
}
function calShift(dir){
  calMonth+=dir;
  if(calMonth<0){calMonth=11;calYear--;}
  if(calMonth>11){calMonth=0;calYear++;}
  renderCal();
}
renderCal();

// ── PLANS ─────────────────────────────────────────────────────────────────────
let _plans=[];
let _activePlanIdx=0;

async function loadPlans(){
  if(window._serverPlans !== undefined){
    _plans = window._serverPlans;
    renderPlans();
    return;
  }
  try{
    const r=await fetch(`${BASE}/api/specialist/vision/plans`).then(r=>r.json());
    _plans=r.plans||[];
    renderPlans();
  }catch(e){ console.error('loadPlans error:',e); renderPlans(); }
}

function renderPlans(){
  const c=document.getElementById('plans-list');
  if(!_plans.length){
    c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:12px">No plans yet. Click + NEW to add one.</div>';
    return;
  }
  c.innerHTML=_plans.map((p,i)=>`
    <div class="plan-card${i===_activePlanIdx?' active':''}" onclick="selectPlan(${i})">
      <div class="plan-title">${esc(p.title)}</div>
      <div class="plan-meta">
        <span class="plan-phase">${esc(p.phase||'PLANNING')}</span>
        <span class="plan-due">DUE ${esc(p.due||'TBD')}</span>
      </div>
    </div>`).join('');
}

function selectPlan(i){
  _activePlanIdx=i;
  renderPlans();
}

async function refreshPlans(){
  // Always re-fetch from server (ignores server-injected snapshot)
  try{
    const r=await fetch(`${BASE}/api/specialist/vision/plans`).then(r=>r.json());
    _plans=r.plans||[];
    renderPlans();
  }catch(e){ console.error('refreshPlans error:',e); }
}

async function savePlans(){
  await fetch(`${BASE}/api/specialist/vision/plans`,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({plans:_plans})});
}

async function newPlan(){
  const t=prompt('Plan title:');if(!t)return;
  const due=prompt('Due date (e.g. May 15):','TBD')||'TBD';
  _plans.unshift({id:Date.now(),title:t,phase:'PLANNING',due,notes:''});
  _activePlanIdx=0;
  renderPlans();
  await savePlans();
}

// ── TIMELINE ─────────────────────────────────────────────────────────────────
async function loadTimeline(){
  const wrap=document.getElementById('timeline-wrap');
  wrap.innerHTML='<div style="text-align:center;color:var(--muted);padding:60px;font-size:12px">Loading calendar…</div>';
  try{
    const r=await fetch(`${BASE}/api/specialist/vision/events?hours=168`).then(r=>r.json());
    const events=r.events||[];
    if(!events.length){
      wrap.innerHTML='<div style="text-align:center;color:var(--muted);padding:60px;font-size:12px">No upcoming events in the next 7 days.</div>';
      return;
    }
    // Mark event dates on mini calendar
    _eventDates=new Set();
    events.forEach(e=>{
      if(e.date){
        // Convert "27 April 2026" → "2026-04-27"
        try{
          const d=new Date(e.date);
          if(!isNaN(d)){
            const key=d.toISOString().slice(0,10);
            _eventDates.add(key);
          }
        }catch(_){}
      }
    });
    renderCal();

    // Group by date
    const byDay={};
    events.forEach(e=>{const day=e.date||'Upcoming';if(!byDay[day])byDay[day]=[];byDay[day].push(e);});

    wrap.innerHTML=Object.entries(byDay).map(([day,evts])=>`
      <div class="timeline-day">
        <div class="day-label">${esc(day).toUpperCase()}</div>
        ${evts.map(e=>`
          <div class="event-row">
            <div class="event-time">${esc(e.time||'ALL DAY')}</div>
            <div class="event-bar ${e.type||'work'}"></div>
            <div class="event-card">
              <div class="event-title">${esc(e.title)}</div>
              ${e.calendar?`<div class="event-detail">${esc(e.calendar)}</div>`:''}
              <span class="event-tag ${e.type||'work'}">${(e.type||'work').toUpperCase()}</span>
              ${e.end_time?`<span class="event-tag work" style="border-color:var(--border);color:var(--muted);margin-left:4px">${esc(e.time)}–${esc(e.end_time)}</span>`:''}
            </div>
          </div>`).join('')}
      </div>`).join('');
  }catch(err){
    wrap.innerHTML='<div style="text-align:center;color:var(--muted);padding:60px;font-size:12px">Calendar not accessible — check macOS Calendar permissions.</div>';
  }
}

// ── AGENDA ────────────────────────────────────────────────────────────────────
async function loadAgenda(){
  const c=document.getElementById('mini-agenda');
  try{
    const r=await fetch(`${BASE}/api/specialist/vision/today`).then(r=>r.json());
    const events=r.events||[];
    if(!events.length){
      c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:8px">No events today.</div>';
      return;
    }
    c.innerHTML=events.map(e=>`
      <div class="agenda-item">
        <div class="agenda-time">${esc(e.time||'ALL DAY')}</div>
        <div class="agenda-title">${esc(e.title)}</div>
      </div>`).join('');
  }catch(_){
    c.innerHTML='<div style="color:var(--muted);font-size:11px;padding:8px">Not connected.</div>';
  }
}

// ── MARKDOWN RENDERER ─────────────────────────────────────────────────────────
function mdToHtml(t){
  t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/^### (.+)$/gm,'<div style="font-size:10px;letter-spacing:2px;color:var(--muted);margin:8px 0 3px;text-transform:uppercase">$1</div>');
  t=t.replace(/^## (.+)$/gm,'<div style="font-size:12px;color:var(--green);letter-spacing:1px;margin:8px 0 4px">$1</div>');
  t=t.replace(/^# (.+)$/gm,'<div style="font-size:13px;font-weight:700;color:var(--green);letter-spacing:2px;margin:8px 0 5px">$1</div>');
  t=t.replace(/\*\*(.+?)\*\*/g,'<strong style="color:var(--text)">$1</strong>');
  t=t.replace(/\*(.+?)\*/g,'<em style="color:var(--text)">$1</em>');
  t=t.replace(/`(.+?)`/g,'<code style="background:var(--bg1);padding:1px 5px;border-radius:2px;font-size:11px">$1</code>');
  t=t.replace(/^[-*•] (.+)$/gm,'<div style="padding-left:14px;margin:2px 0">· $1</div>');
  t=t.replace(/^\d+\. (.+)$/gm,'<div style="padding-left:14px;margin:2px 0">$1</div>');
  t=t.replace(/\|(.+)\|/g,'<div style="font-size:10px;color:var(--muted);padding:2px 0">$1</div>');
  t=t.replace(/\n\n/g,'<br>').replace(/\n/g,'<br>');
  return t;
}

// ── COMMAND ───────────────────────────────────────────────────────────────────
function cmdKey(e){if(e.key==='Enter')sendCmd();}
async function sendCmd(){
  const inp=document.getElementById('cmd-input');
  const text=inp.value.trim();if(!text)return;
  inp.value='';
  const wrap=document.getElementById('timeline-wrap');
  // Show user query
  const uDiv=document.createElement('div');
  uDiv.style.cssText='background:rgba(0,204,102,.06);border:1px solid var(--border);border-left:3px solid var(--muted);padding:8px 12px;margin:6px 0;border-radius:3px;font-size:11px;color:var(--muted)';
  uDiv.textContent='You: '+text;
  wrap.prepend(uDiv);
  try{
    const r=await fetch(`${BASE}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:'[VISION] '+text})});
    const d=await r.json();
    const div=document.createElement('div');
    div.style.cssText='background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--green);padding:12px;margin:6px 0;border-radius:3px;font-size:12px;line-height:1.6';
    div.innerHTML=mdToHtml(d.response||d.message||'Done.');
    wrap.prepend(div);
  }catch(e){console.error(e);}
}

// ── INIT ──────────────────────────────────────────────────────────────────────
loadPlans();
loadTimeline();
loadAgenda();
setInterval(loadTimeline, 5*60*1000);
setInterval(loadAgenda, 60*1000);
setInterval(refreshPlans, 10*1000);  // re-check plans every 10s (picks up voice-saved plans)
</script>
</body>
</html>"""
