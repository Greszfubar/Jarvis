"""JARVIS Dashboard JavaScript — full UI redesign v2"""

_SCRIPT = r"""<script>
// ─── UTILS ───────────────────────────────────────────────────────────────────
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

// ─── WEBSOCKET ────────────────────────────────────────────────────────────────
let ws;
function connect(){
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onopen  = ()=>{ console.log('WS connected'); };
  ws.onclose = ()=>{ setTimeout(connect, 3000); };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if(d.kind==='typing')     { showTyping(); setCoreState('thinking'); }
    else if(d.kind==='response'){ hideTyping(); setCoreState('idle'); addMsg('assistant',d.text); enableInput(); enterConversationMode(); }
    else if(d.kind==='alert')   { addMsg('assistant','⚠ '+d.message); }
    else if(d.kind==='task_done'){ addMsg('assistant','✓ Task complete: '+d.title); }
  };
}
connect();

// ─── CHAT ─────────────────────────────────────────────────────────────────────
const chatEl = document.getElementById('chat-scroll');
let typingEl = null;
function addMsg(role,text){
  const d=document.createElement('div'); d.className='msg '+role; d.textContent=text;
  chatEl.appendChild(d); chatEl.scrollTop=chatEl.scrollHeight;
}
function showTyping(){
  if(typingEl) return;
  typingEl=document.createElement('div'); typingEl.className='msg assistant';
  typingEl.innerHTML='JARVIS ▸  <span class="typing-dot">▋</span>';
  chatEl.appendChild(typingEl); chatEl.scrollTop=chatEl.scrollHeight;
}
function hideTyping(){ if(typingEl){typingEl.remove();typingEl=null;} }
function disableInput(){ document.getElementById('cmd-input').disabled=true; }
function enableInput(){
  document.getElementById('cmd-input').disabled=false;
  if(!_standbyActive) document.getElementById('cmd-input').focus();
}
function sendMsg(){
  const inp=document.getElementById('cmd-input'); const msg=inp.value.trim();
  if(!msg||!ws||ws.readyState!==1) return;
  inp.value=''; addMsg('user',msg); ws.send(msg); disableInput();
}
document.getElementById('cmd-input').addEventListener('keydown',e=>{ if(e.key==='Enter') sendMsg(); });

// ─── CORE STATE ───────────────────────────────────────────────────────────────
let _convModeTimer=null;
function setCoreState(s){
  const glow=document.getElementById('core-glow');
  const badge=document.getElementById('conv-badge');
  if(s==='thinking') glow.style.background='radial-gradient(circle,rgba(255,200,0,.2) 0%,transparent 70%)';
  else if(s==='listening') glow.style.background='radial-gradient(circle,rgba(0,255,136,.2) 0%,transparent 70%)';
  else if(s==='conversation') glow.style.background='radial-gradient(circle,rgba(0,180,255,.18) 0%,transparent 70%)';
  else glow.style.background='radial-gradient(circle,rgba(0,212,255,.15) 0%,transparent 70%)';
  if(badge) badge.style.opacity=(s==='conversation')?'1':'0';
}
function enterConversationMode(){
  setCoreState('conversation');
  if(_convModeTimer) clearTimeout(_convModeTimer);
  _convModeTimer=setTimeout(()=>setCoreState('idle'),30000);
}
function exitConversationMode(){
  if(_convModeTimer){clearTimeout(_convModeTimer);_convModeTimer=null;}
  setCoreState('idle');
}

// ─── AUDIO VISUALIZER ─────────────────────────────────────────────────────────
const canvas=document.getElementById('viz-canvas');
const ctx2d=canvas.getContext('2d');
let analyser,timeDomain,freqDomain,audioReady=false;
function resizeCanvas(){ canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight; }
window.addEventListener('resize',resizeCanvas); resizeCanvas();
async function initAudio(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    const ac=new(window.AudioContext||window.webkitAudioContext)();
    const src=ac.createMediaStreamSource(stream);
    analyser=ac.createAnalyser(); analyser.fftSize=1024; analyser.smoothingTimeConstant=0.82;
    src.connect(analyser);
    timeDomain=new Uint8Array(analyser.fftSize); freqDomain=new Uint8Array(analyser.frequencyBinCount);
    audioReady=true;
  }catch(e){ console.log('Mic blocked — idle animation'); }
  requestAnimationFrame(drawViz);
}
let idleT=0;
function drawViz(){
  requestAnimationFrame(drawViz);
  const W=canvas.width,H=canvas.height,cx=W/2,cy=H/2;
  ctx2d.clearRect(0,0,W,H);
  const waveW=W*.72,waveX=(W-waveW)/2,waveAmp=Math.min(H*.18,80),N=audioReady?timeDomain.length:256;
  if(audioReady) analyser.getByteTimeDomainData(timeDomain);
  function sampleAt(i,total){
    if(audioReady){ const idx=Math.floor(i/total*timeDomain.length); return(timeDomain[idx]/128.0)-1.0; }
    const p=i/total;
    return .12*Math.sin(idleT*1.4+p*8)+.06*Math.sin(idleT*2.3+p*14)+.03*Math.sin(idleT*3.7+p*22);
  }
  ctx2d.save(); ctx2d.shadowBlur=8; ctx2d.shadowColor='rgba(0,212,255,0.5)';
  const pts=220;
  function drawWaveLine(yBase,flip,alpha){
    ctx2d.beginPath();
    for(let i=0;i<=pts;i++){
      const x=waveX+(i/pts)*waveW,s=sampleAt(i,pts),y=yBase+s*waveAmp*(flip?-1:1);
      i===0?ctx2d.moveTo(x,y):ctx2d.lineTo(x,y);
    }
    ctx2d.strokeStyle=`rgba(0,212,255,${alpha})`; ctx2d.lineWidth=1.5; ctx2d.stroke();
  }
  drawWaveLine(cy-14,false,.55); drawWaveLine(cy+14,true,.35); ctx2d.restore();
  ctx2d.save(); ctx2d.strokeStyle='rgba(0,119,170,0.25)'; ctx2d.lineWidth=.5; ctx2d.setLineDash([2,6]);
  ctx2d.beginPath(); ctx2d.moveTo(waveX,cy); ctx2d.lineTo(waveX+waveW,cy); ctx2d.stroke(); ctx2d.setLineDash([]); ctx2d.restore();
  const coreR=Math.min(W,H)*.135,ringPts=180; let maxDisp=0;
  ctx2d.save(); ctx2d.shadowBlur=14; ctx2d.shadowColor='rgba(0,212,255,0.4)';
  function drawRing(radiusBase,scale,alpha){
    ctx2d.beginPath();
    for(let i=0;i<=ringPts;i++){
      const angle=(i/ringPts)*Math.PI*2-Math.PI/2,s=sampleAt(i,ringPts),r=radiusBase+s*scale;
      if(i===0) maxDisp=0; maxDisp=Math.max(maxDisp,Math.abs(s));
      const x=cx+Math.cos(angle)*r,y=cy+Math.sin(angle)*r;
      i===0?ctx2d.moveTo(x,y):ctx2d.lineTo(x,y);
    }
    ctx2d.closePath();
    ctx2d.strokeStyle=audioReady&&maxDisp>.3?`rgba(0,255,136,${alpha})`:`rgba(0,212,255,${alpha})`;
    ctx2d.lineWidth=1.8; ctx2d.stroke();
  }
  drawRing(coreR+22,28,.7); drawRing(coreR+44,18,.3); ctx2d.restore();
  if(audioReady){
    analyser.getByteFrequencyData(freqDomain);
    const bass=freqDomain.slice(0,8).reduce((a,b)=>a+b,0)/8/255;
    if(bass>.1){
      ctx2d.save(); ctx2d.beginPath(); ctx2d.arc(cx,cy,coreR*.5+bass*30,0,Math.PI*2);
      ctx2d.fillStyle=`rgba(0,212,255,${bass*.12})`; ctx2d.fill(); ctx2d.restore();
    }
    if(maxDisp>.25) setCoreState('listening'); else setCoreState('idle');
  }
  idleT+=.025;
}
initAudio();

// ─── BROWSER AUDIO CAPTURE ────────────────────────────────────────────────────
let audioWs=null,_jarvisSpeaking=false,_audioCtx=null,_speakingTimer=null;
function downsampleTo16k(float32,inputRate){
  if(inputRate===16000){ const out=new Int16Array(float32.length); for(let i=0;i<float32.length;i++) out[i]=Math.max(-32768,Math.min(32767,float32[i]*32768)); return out; }
  const ratio=inputRate/16000,outLen=Math.floor(float32.length/ratio),out=new Int16Array(outLen);
  for(let i=0;i<outLen;i++){ const src=float32[Math.floor(i*ratio)]; out[i]=Math.max(-32768,Math.min(32767,src*32768)); }
  return out;
}
async function startAudioCapture(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    _audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    if(_audioCtx.state==='suspended') await _audioCtx.resume();
    const source=_audioCtx.createMediaStreamSource(stream);
    const proc=_audioCtx.createScriptProcessor(4096,1,1);
    source.connect(proc); proc.connect(_audioCtx.destination);
    function openAudioWs(){ audioWs=new WebSocket(`ws://${location.host}/ws/audio`); audioWs.binaryType='arraybuffer'; audioWs.onclose=()=>setTimeout(openAudioWs,2000); audioWs.onerror=()=>audioWs.close(); }
    openAudioWs();
    proc.onaudioprocess=e=>{ if(!audioWs||audioWs.readyState!==1) return; if(_jarvisSpeaking&&!_standbyActive) return; audioWs.send(downsampleTo16k(e.inputBuffer.getChannelData(0),_audioCtx.sampleRate).buffer); };
    const hint=document.getElementById('standby-mic-hint'); if(hint) hint.textContent='● MIC ACTIVE';
  }catch(err){ console.warn('Audio capture failed:',err.message); }
}
startAudioCapture();
function _setSpeaking(val){ _jarvisSpeaking=val; clearTimeout(_speakingTimer); if(val) _speakingTimer=setTimeout(()=>{_jarvisSpeaking=false;},30000); }

// Override WS handler for voice events
const _origOnMessage=ws.onmessage;
ws.onmessage=e=>{
  const d=JSON.parse(e.data);
  if(d.kind==='clap_detected'){ const cp=document.getElementById('standby-clap'); if(cp){cp.style.opacity='1';setTimeout(()=>cp.style.opacity='0',5000);} }
  else if(d.kind==='launching'){ const msg=document.getElementById('standby-msg'); if(msg) msg.textContent='ACTIVATING…'; setTimeout(dismissStandby,1200); }
  else if(d.kind==='wake'){ exitConversationMode(); setCoreState('listening'); }
  else if(d.kind==='waiting_command'){ setCoreState('listening'); addMsg('assistant','…listening for command…'); }
  else if(d.kind==='got_command'){ exitConversationMode(); setCoreState('thinking'); }
  else if(d.kind==='speaking'){ _setSpeaking(true); exitConversationMode(); setCoreState('thinking'); if(d.text) startWordAnimation(d.text); }
  else if(d.kind==='speaking_done'){ _setSpeaking(false); stopWordAnimation(); enterConversationMode(); }
  if(['typing','response','alert','task_done','briefing','gmail','calendar'].includes(d.kind)){
    if(d.kind==='typing'){showTyping();setCoreState('thinking');}
    else if(d.kind==='response'){hideTyping();addMsg('assistant',d.text);enableInput();enterConversationMode();}
    else if(d.kind==='alert'){addMsg('assistant','⚠ '+(d.message||''));}
    else if(d.kind==='task_done'){addMsg('assistant','✓ Task complete: '+d.title);}
  }
};

// ─── STANDBY ──────────────────────────────────────────────────────────────────
let _standbyActive=true,_sbPulse=0;
function dismissStandby(){ _standbyActive=false; const ov=document.getElementById('standby-overlay'); if(ov){ov.style.opacity='0';setTimeout(()=>ov.style.display='none',800);} }
function standbyClick(e){ if(_audioCtx&&_audioCtx.state==='suspended') _audioCtx.resume().then(()=>{ const h=document.getElementById('standby-mic-hint'); if(h) h.textContent='● MIC ACTIVE'; }); }
function sbShowUnlock(){ const w=document.getElementById('sb-unlock-wrap'); if(!w) return; w.style.display=w.style.display==='none'?'flex':'none'; if(w.style.display==='flex') setTimeout(()=>document.getElementById('sb-pw')?.focus(),50); }
async function sbUnlock(){ const pw=document.getElementById('sb-pw')?.value||''; const r=await fetch('/api/tools?password='+encodeURIComponent(pw)).then(r=>r.json()).catch(()=>({error:'fail'})); if(r.error){const err=document.getElementById('sb-pw-err');if(err){err.style.display='';setTimeout(()=>err.style.display='none',2000);}return;} await fetch('/api/standby/activate',{method:'POST'}).catch(()=>{}); dismissStandby(); }
setInterval(()=>{ if(!_standbyActive) return; _sbPulse=(_sbPulse+1)%3; for(let i=0;i<3;i++){const d=document.getElementById('sb-dot'+(i+1));if(d)d.style.background=i===_sbPulse?'#00d4ff':'#0a3a5a';} },500);
document.addEventListener('DOMContentLoaded',()=>{ const inp=document.getElementById('cmd-input'); if(inp) inp.addEventListener('keydown',e=>{if(e.key==='Enter'&&inp.value.trim()) dismissStandby();}); });

// ─── MUTE ─────────────────────────────────────────────────────────────────────
let _micMuted=false;
async function toggleMute(){
  _micMuted=!_micMuted;
  const btn=document.getElementById('mute-btn');
  if(btn){btn.textContent=_micMuted?'🔇':'🎙';btn.style.color=_micMuted?'var(--red)':'var(--muted)';btn.style.borderColor=_micMuted?'var(--red)':'var(--border)';btn.title=_micMuted?'Mic muted':'Mute microphone';}
  await fetch('/api/mute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({muted:_micMuted})});
  _jarvisSpeaking=_micMuted;
}

// ─── WORD ANIMATION ───────────────────────────────────────────────────────────
let _wordAnimTimer=null;
function startWordAnimation(text){
  const el=document.getElementById('speaking-text'); if(!el||!text) return;
  if(_wordAnimTimer){clearTimeout(_wordAnimTimer);_wordAnimTimer=null;}
  const words=text.trim().split(/\s+/);
  el.innerHTML=words.map((w,i)=>`<span class="spoken-word" id="sw${i}">${esc(w)}</span>`).join(' ');
  el.classList.add('active');
  words.forEach((_,i)=>{ _wordAnimTimer=setTimeout(()=>{const sp=document.getElementById('sw'+i);if(sp)sp.classList.add('said');},i*460); });
}
function stopWordAnimation(){ const el=document.getElementById('speaking-text'); if(el){el.classList.remove('active');el.innerHTML='';} if(_wordAnimTimer){clearTimeout(_wordAnimTimer);_wordAnimTimer=null;} }

// ─── STATUS POLL ──────────────────────────────────────────────────────────────
async function pollStatus(){
  try{
    const d=await(await fetch('/api/status')).json();
    const w=d.weather||{};
    document.getElementById('bb-w-temp').textContent=w.temp!==undefined?Math.round(w.temp)+'°C':'—';
    document.getElementById('bb-w-cond').textContent=(w.description||w.condition||'—').toLowerCase();
    document.getElementById('bb-w-wind').textContent=w.wind_speed!==undefined?Math.round(w.wind_speed)+' m/s wind':'— wind';
    document.getElementById('bb-w-humid').textContent=w.humidity!==undefined?w.humidity+'% humid':'— humid';
    try{
      const td=await(await fetch('/api/tasks')).json();
      const tasks=td.tasks||[];
      const open=tasks.filter(t=>t.status!=='done').length;
      const urgent=tasks.filter(t=>t.priority==='urgent'&&t.status!=='done').length;
      const done=tasks.filter(t=>t.status==='done').length;
      document.getElementById('bb-t-open').textContent=open;
      document.getElementById('bb-t-sub').textContent=open===1?'1 open task':open+' open tasks';
      const urgEl=document.getElementById('bb-t-urgent');
      urgEl.textContent=urgent+' URGENT'; urgEl.style.display=urgent>0?'':'none';
      document.getElementById('bb-t-done').textContent=done+' done';
    }catch(e){}
    document.getElementById('bb-bot-tasks').textContent=(d.tasks||0)+' tasks tracked';
    const evts=d.calendar||[];
    document.getElementById('bb-c-count').textContent=evts.length+' events';
    if(evts.length){ const next=evts[0]; document.getElementById('bb-c-next').textContent=(next.title||'Event').slice(0,28); const dt=next.start?new Date(next.start):null; document.getElementById('bb-c-time').textContent=dt?dt.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}):'—'; }
    else{ document.getElementById('bb-c-next').textContent='No events today'; document.getElementById('bb-c-time').textContent='—'; }
    const unread=d.unread||0;
    document.getElementById('bb-i-count').textContent=unread+' unread';
    document.getElementById('bb-i-sub').textContent=unread===0?'Inbox clear':unread+' messages waiting';
    const impEl=document.getElementById('bb-i-imp'); impEl.textContent=unread+' HIGH PRIORITY'; impEl.style.display=unread>0?'':'none';
    const nl=document.getElementById('news-list');
    if(d.news&&d.news.length) nl.innerHTML=d.news.map(n=>`<div class="news-item" ${n.url?`onclick="openUrl('${esc(n.url)}')" title="Open article"`:''}><div class="news-title">${esc(n.title||'')}</div><div class="news-src">${esc(n.source||'')}</div></div>`).join('');
  }catch(e){}
}
pollStatus(); setInterval(pollStatus,30000);

// ─── CRYPTO POLL ──────────────────────────────────────────────────────────────
const COIN_LABELS={bitcoin:'BTC',ethereum:'ETH',solana:'SOL',cardano:'ADA',dogecoin:'DOGE'};
async function pollCrypto(){
  try{
    const d=await(await fetch('/api/crypto')).json();
    const el=document.getElementById('crypto-list');
    const html=Object.entries(COIN_LABELS).map(([id,sym])=>{
      const coin=d[id]; if(!coin) return '';
      const chg=coin.usd_24h_change||0,cls=chg>=0?'up':'dn',sign=chg>=0?'+':'';
      const price=coin.usd>=1000?'$'+Math.round(coin.usd).toLocaleString():'$'+coin.usd.toFixed(4);
      return `<div class="crypto-row"><span class="crypto-sym">${sym}</span><span class="crypto-price">${price}</span><span class="crypto-chg ${cls}">${sign}${chg.toFixed(1)}%</span></div>`;
    }).join('');
    el.innerHTML=html||'<div class="empty">No data</div>';
  }catch(e){}
}
pollCrypto(); setInterval(pollCrypto,60000);

// ─── MODAL SYSTEM ─────────────────────────────────────────────────────────────
let currentModal=null;
function openModal(name){
  currentModal=name;
  document.getElementById('modal-overlay').classList.add('open');
  const titles={weather:'WEATHER — PETERSFIELD, UK',tasks:'TASK BOARD',bots:'AGENT NETWORK',
    calendar:'CALENDAR',inbox:'INBOX',brain:'MEMORY & BRAIN',robot:'AGENT DETAIL',settings:'SETTINGS'};
  document.getElementById('modal-title').textContent=titles[name]||name.toUpperCase();
  const body=document.getElementById('modal-body');
  body.innerHTML='<div class="empty">Loading…</div>';
  const loaders={weather:loadWeatherModal,tasks:loadTasksModal,bots:loadBotsModal,
    calendar:loadCalendarModal,inbox:loadInboxModal,brain:loadBrainModal,
    robot:loadRobotModal,settings:loadSettingsModal};
  if(loaders[name]) loaders[name](body);
}
function closeModal(){ document.getElementById('modal-overlay').classList.remove('open'); currentModal=null; hideCalCtx(); }
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){closeModal();closeTaskPopup();closeCepPopup();hideCalCtx();} });

function launchAgent(name){
  if(window.pywebview&&window.pywebview.api) window.pywebview.api.open_app(name);
  else window.open('/'+name,'_blank');
}
function openUrl(url){ if(!url) return; if(window.pywebview&&window.pywebview.api) window.pywebview.api.open_url(url); else window.open(url,'_blank'); }

// ─── WEATHER MODAL ────────────────────────────────────────────────────────────
async function loadWeatherModal(body){
  const d=await(await fetch('/api/status')).json();
  const w=d.weather||{},fc=d.forecast||[];
  const days=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const fcHtml=fc.slice(0,7).map(f=>{const dt=f.date?new Date(f.date):null;return`<div class="fc-day"><div class="fc-day-name">${dt?days[dt.getDay()]:'—'}</div><div class="fc-day-temp">${Math.round(f.temp_max||f.temp||0)}°</div><div class="fc-day-desc">${esc((f.description||'').slice(0,10))}</div></div>`;}).join('');
  body.innerHTML=`<div class="weather-big"><div class="w-temp">${w.temp!==undefined?Math.round(w.temp)+'°C':'—'}</div><div class="w-desc">${esc((w.description||w.condition||'—').toUpperCase())}</div><div class="w-city">PETERSFIELD, UK</div></div><div class="w-grid"><div class="w-card"><div class="w-card-label">FEELS LIKE</div><div class="w-card-val">${w.feels_like!==undefined?Math.round(w.feels_like)+'°C':'—'}</div></div><div class="w-card"><div class="w-card-label">HUMIDITY</div><div class="w-card-val">${w.humidity!==undefined?w.humidity+'%':'—'}</div></div><div class="w-card"><div class="w-card-label">WIND</div><div class="w-card-val">${w.wind_speed!==undefined?w.wind_speed+' m/s':'—'}</div></div><div class="w-card"><div class="w-card-label">LOCATION</div><div class="w-card-val" style="font-size:11px">PO34, Hampshire</div></div></div>${fcHtml?`<div style="margin-top:16px;font-size:9px;color:var(--muted);letter-spacing:2px">7-DAY FORECAST</div><div class="forecast-row">${fcHtml}</div>`:''}`;
}

// ─── TASKS MODAL ──────────────────────────────────────────────────────────────
let _taskFilter='all', _dragTask=null;
async function loadTasksModal(body){
  body.style.display='flex'; body.style.flexDirection='column'; body.style.height='100%'; body.style.padding='16px 20px';
  body.innerHTML=`
    <div class="task-header">
      <div class="task-slider">
        <button class="ts-btn active" onclick="setTaskFilter('all',this)">ALL</button>
        <button class="ts-btn" onclick="setTaskFilter('jarvis',this)">JARVIS</button>
        <button class="ts-btn" onclick="setTaskFilter('mine',this)">MY TASKS</button>
      </div>
      <button class="btn" onclick="openTaskPopup()">+ NEW TASK</button>
    </div>
    <div class="kanban" id="kanban-board" style="flex:1"><div class="empty">Loading…</div></div>`;
  await refreshKanban();
}

function setTaskFilter(f,btn){
  _taskFilter=f;
  document.querySelectorAll('.ts-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  refreshKanban();
}

const KCOLS=[
  {key:'todo',label:'TO DO',c:'var(--muted)'},
  {key:'in_progress',label:'IN PROGRESS',c:'var(--c1)'},
  {key:'blocked',label:'BLOCKED',c:'var(--red)'},
  {key:'done',label:'DONE',c:'var(--green)'}
];

async function refreshKanban(){
  try{
    const td=await(await fetch('/api/tasks')).json();
    let tasks=(td.tasks||[]);
    // Filter by slider — no reminders
    if(_taskFilter==='jarvis') tasks=tasks.filter(t=>t.assignee==='jarvis');
    else if(_taskFilter==='mine') tasks=tasks.filter(t=>t.assignee!=='jarvis');
    else{
      // All: human tasks first, then JARVIS
      tasks=[...tasks.filter(t=>t.assignee!=='jarvis'),...tasks.filter(t=>t.assignee==='jarvis')];
    }
    const byS={todo:[],in_progress:[],blocked:[],done:[]};
    tasks.forEach(t=>(byS[t.status]||byS.todo).push(t));
    document.getElementById('kanban-board').innerHTML=KCOLS.map(col=>`
      <div class="k-col" id="kcol-${col.key}" data-col="${col.key}"
           ondragover="kDragOver(event,this)" ondrop="kDrop(event,this)" ondragleave="kDragLeave(this)">
        <div class="k-head" style="color:${col.c}">${col.label}<span style="color:var(--muted)">${(byS[col.key]||[]).length}</span></div>
        <div class="k-body">
          ${(byS[col.key]||[]).map(t=>{
            const who=t.assignee==='jarvis'?'jarvis':'human',pri=t.priority||'medium';
            return `<div class="task-card ${who} ${pri==='urgent'?'urgent':''}"
                draggable="true" data-id="${t.id||''}" data-status="${t.status||'todo'}"
                ondragstart="kDragStart(event,this)" ondragend="kDragEnd(event,this)">
              <button class="tc-delete" onclick="deleteTask(${t.id},event)" title="Delete">✕</button>
              <div class="tc-title">${esc(t.title)}</div>
              <div class="tc-meta">
                <span class="tc-tag ${pri}">${pri.toUpperCase()}</span>
                <span class="tc-tag ${who}">${who==='jarvis'?'JARVIS':'ME'}</span>
                ${t.due?`<span class="tc-tag">${esc(t.due.slice(0,10))}</span>`:''}
                ${t.category&&t.category!=='general'?`<span class="tc-tag">${esc(t.category)}</span>`:''}
              </div>
              ${t.result?`<div class="tc-result">${esc(t.result.slice(0,80))}</div>`:''}
            </div>`;
          }).join('')||`<div class="empty">Empty</div>`}
        </div>
      </div>`).join('');
  }catch(e){ const b=document.getElementById('kanban-board'); if(b) b.innerHTML='<div class="empty">Error loading tasks</div>'; }
}

async function deleteTask(id,e){
  if(e){e.stopPropagation();e.preventDefault();}
  if(!id) return;
  await fetch('/api/tasks/'+id,{method:'DELETE'}).catch(()=>{});
  refreshKanban();
}

function kDragStart(e,el){ _dragTask=el; el.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; e.dataTransfer.setData('text/plain',el.dataset.id); document.getElementById('k-delete-zone').classList.add('visible'); }
function kDragEnd(e,el){ el.classList.remove('dragging'); _dragTask=null; document.getElementById('k-delete-zone').classList.remove('visible','hot'); document.querySelectorAll('.k-col').forEach(c=>c.classList.remove('drag-over')); }
function kDragOver(e,col){ e.preventDefault(); e.dataTransfer.dropEffect='move'; document.querySelectorAll('.k-col').forEach(c=>c.classList.remove('drag-over')); col.classList.add('drag-over'); const dz=document.getElementById('k-delete-zone'); if(dz){const rect=dz.getBoundingClientRect(); if(e.clientY>rect.top-30) dz.classList.add('hot'); else dz.classList.remove('hot');} }
function kDragLeave(col){ col.classList.remove('drag-over'); }
async function kDrop(e,col){
  e.preventDefault(); col.classList.remove('drag-over');
  if(!_dragTask) return;
  const id=_dragTask.dataset.id,newStatus=col.dataset.col;
  const dz=document.getElementById('k-delete-zone');
  if(dz){const rect=dz.getBoundingClientRect(); if(e.clientY>rect.top-30){if(confirm('Delete this task?')){await fetch('/api/tasks/'+id,{method:'DELETE'}).catch(()=>{}); await refreshKanban();} dz.classList.remove('visible','hot'); return;}}
  if(id&&newStatus) await fetch('/api/tasks/'+id+'/status',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:newStatus})}).catch(()=>{});
  await refreshKanban();
}
document.addEventListener('DOMContentLoaded',()=>{
  const dz=document.getElementById('k-delete-zone');
  if(dz){
    dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('hot');});
    dz.addEventListener('dragleave',()=>dz.classList.remove('hot'));
    dz.addEventListener('drop',async e=>{e.preventDefault();if(_dragTask){const id=_dragTask.dataset.id;if(id)await fetch('/api/tasks/'+id,{method:'DELETE'}).catch(()=>{});await refreshKanban();}dz.classList.remove('visible','hot');});
  }
});

// ─── TASK POPUP ───────────────────────────────────────────────────────────────
function openTaskPopup(){
  document.getElementById('task-popup-overlay').classList.add('open');
  setTimeout(()=>document.getElementById('tp-title-input')?.focus(),50);
}
function closeTaskPopup(){
  document.getElementById('task-popup-overlay').classList.remove('open');
  document.getElementById('tp-title-input').value='';
  document.getElementById('tp-date').value='';
}
async function submitTaskPopup(){
  const title=document.getElementById('tp-title-input').value.trim();
  const pri=document.getElementById('tp-pri').value;
  const who=document.getElementById('tp-who').value;
  const dueDate=document.getElementById('tp-date').value;
  if(!title) return;
  await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title,priority:pri,assignee:who,category:'general',due:dueDate||null})});
  closeTaskPopup();
  setTimeout(refreshKanban,300);
}

// ─── JARVIS AUTO TASK (every 20 min) ─────────────────────────────────────────
async function jarvisAutoTask(){
  try{ await fetch('/api/tasks/jarvis-auto',{method:'POST'}); }catch(e){}
}
setInterval(jarvisAutoTask, 20*60*1000);

// ─── BOTS / AGENT NETWORK MODAL ───────────────────────────────────────────────
const ANT_AGENTS=[
  {id:'ultron', name:'ULTRON', color:'#cc0000', desc:'Security & threat intelligence — monitors breaches, scans, watchlist', app:'ultron'},
  {id:'vision', name:'VISION', color:'#00cc66', desc:'Intelligence & strategic planning — calendar, plans, briefings', app:'vision'},
  {id:'friday', name:'FRIDAY', color:'#4488ff', desc:'Content & research — newspaper, blogs, news curation', app:'friday'},
  {id:'gresz',  name:'GRESZ',  color:'#c8a840', desc:'Business intelligence — clients, projects, pipeline', app:'gresz'},
];
let _antPulses=[], _antAnimFrame=null, _antAgentTasks={jarvis:[],ultron:[],vision:[],friday:[],gresz:[]};

async function loadBotsModal(body){
  body.style.padding='0'; body.style.overflow='hidden';
  body.innerHTML=`<div style="display:flex;flex-direction:column;height:100%;padding:16px 20px;gap:0;overflow:hidden">
    <!-- JARVIS node -->
    <div style="display:flex;justify-content:center;margin-bottom:8px;flex-shrink:0">
      <div id="ant-jarvis" style="background:var(--bg2);border:1px solid var(--c1);border-radius:3px;padding:14px 20px;min-width:280px;box-shadow:0 0 20px rgba(0,212,255,.15);text-align:center">
        <div style="font-size:14px;font-weight:700;letter-spacing:3px;color:var(--c1);margin-bottom:4px">JARVIS</div>
        <div style="font-size:9px;color:var(--muted);margin-bottom:10px">Central orchestrator — language, memory, tools, voice & autonomous task management</div>
        <div id="ant-jarvis-tasks" style="display:flex;flex-direction:column;gap:3px;min-height:24px"></div>
      </div>
    </div>
    <!-- Canvas for connection lines -->
    <div style="flex:1;position:relative;min-height:0">
      <canvas id="ant-canvas" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0"></canvas>
      <!-- Agent nodes row -->
      <div style="position:absolute;bottom:8px;left:0;right:0;display:flex;gap:12px;justify-content:center;z-index:1">
        ${ANT_AGENTS.map(a=>`
          <div id="ant-${a.id}" onclick="launchAgent('${a.app}')"
            style="background:var(--bg2);border:1px solid var(--border);border-radius:3px;padding:12px 14px;flex:1;max-width:220px;cursor:pointer;transition:border-color .2s,box-shadow .2s"
            onmouseover="this.style.borderColor='${a.color}';this.style.boxShadow='0 0 14px ${a.color}33'"
            onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow=''">
            <div style="font-size:11px;font-weight:700;letter-spacing:2px;color:${a.color};margin-bottom:3px">${a.name}</div>
            <div style="font-size:8px;color:var(--muted);margin-bottom:8px;line-height:1.4">${a.desc}</div>
            <div id="ant-${a.id}-tasks" style="display:flex;flex-direction:column;gap:3px;min-height:16px"></div>
          </div>`).join('')}
      </div>
    </div>
  </div>`;

  // Load tasks into agent boxes
  await _antLoadTasks();
  // Start animation loop
  if(_antAnimFrame) cancelAnimationFrame(_antAnimFrame);
  _antDraw();
  // Demo: trigger random pulses every 6s
  _antDemoInterval = setInterval(_antTriggerDemo, 6000);
}

let _antDemoInterval=null;
let _antDemoIdx=0;
function _antTriggerDemo(){
  if(!document.getElementById('ant-canvas')) { clearInterval(_antDemoInterval); return; }
  const agents=['ultron','vision','friday','gresz'];
  const agent=agents[_antDemoIdx % agents.length];
  _antDemoIdx++;
  _antFirePulse(agent, 'to', ()=>{
    setTimeout(()=>_antFirePulse(agent,'from',null),1500);
  });
}

function _antFirePulse(agentId, direction, onComplete){
  _antPulses.push({agentId, direction, progress:0, onComplete, startTime:Date.now()});
}

function _antDraw(){
  const canvas=document.getElementById('ant-canvas');
  if(!canvas){_antAnimFrame=null;return;}
  _antAnimFrame=requestAnimationFrame(_antDraw);
  const W=canvas.offsetWidth, H=canvas.offsetHeight;
  if(canvas.width!==W||canvas.height!==H){canvas.width=W;canvas.height=H;}
  const ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,W,H);

  // Get JARVIS node center-bottom
  const jarvisEl=document.getElementById('ant-jarvis');
  if(!jarvisEl) return;
  const containerRect=canvas.getBoundingClientRect();
  const jRect=jarvisEl.getBoundingClientRect();
  const jx=jRect.left-containerRect.left+jRect.width/2;
  const jy=jRect.top-containerRect.top+jRect.height;

  // For each agent, draw connection line
  ANT_AGENTS.forEach(agent=>{
    const el=document.getElementById('ant-'+agent.id);
    if(!el) return;
    const aRect=el.getBoundingClientRect();
    const ax=aRect.left-containerRect.left+aRect.width/2;
    const ay=aRect.top-containerRect.top;

    // Check if there's an active pulse for this agent
    const activePulse=_antPulses.find(p=>p.agentId===agent.id&&p.progress<1);
    const isDone=_antPulses.some(p=>p.agentId===agent.id&&p.direction==='from'&&p.progress>0);

    // Draw line
    ctx.save();
    if(activePulse){
      ctx.strokeStyle=activePulse.direction==='from'?'#00ff88':agent.color;
      ctx.lineWidth=1.5;
      ctx.shadowColor=activePulse.direction==='from'?'#00ff88':agent.color;
      ctx.shadowBlur=8;
      ctx.setLineDash([]);
    } else if(isDone){
      ctx.strokeStyle='rgba(0,255,136,0.4)'; ctx.lineWidth=1; ctx.setLineDash([]);
    } else {
      ctx.strokeStyle='rgba(10,58,90,0.7)'; ctx.lineWidth=1; ctx.setLineDash([5,7]);
    }
    ctx.beginPath(); ctx.moveTo(jx,jy); ctx.lineTo(ax,ay); ctx.stroke();
    ctx.setLineDash([]); ctx.restore();

    // Draw pulse dot
    if(activePulse){
      const t=activePulse.progress;
      const px=activePulse.direction==='to'?jx+(ax-jx)*t:ax+(jx-ax)*t;
      const py=activePulse.direction==='to'?jy+(ay-jy)*t:ay+(jy-ay)*t;
      ctx.save();
      ctx.beginPath(); ctx.arc(px,py,5,0,Math.PI*2);
      ctx.fillStyle=activePulse.direction==='from'?'#00ff88':agent.color;
      ctx.shadowColor=activePulse.direction==='from'?'#00ff88':agent.color;
      ctx.shadowBlur=12; ctx.fill(); ctx.restore();
    }
  });

  // Advance pulses
  const now=Date.now();
  _antPulses=_antPulses.filter(p=>{
    const elapsed=(now-p.startTime)/1000;
    p.progress=Math.min(1, elapsed/1.2);
    if(p.progress>=1){if(p.onComplete) p.onComplete(); return false;}
    return true;
  });
}

async function _antLoadTasks(){
  try{
    const td=await(await fetch('/api/tasks')).json();
    const tasks=td.tasks||[];
    // JARVIS tasks (top 3 active)
    const jTasks=tasks.filter(t=>t.assignee==='jarvis'&&t.status!=='done').slice(0,3);
    const jEl=document.getElementById('ant-jarvis-tasks');
    if(jEl) jEl.innerHTML=jTasks.length?jTasks.map(t=>`<div style="font-size:8px;padding:2px 6px;border-left:2px solid var(--c1);color:var(--c1);background:rgba(0,212,255,.06)">${esc(t.title.slice(0,40))}</div>`).join(''):'<div style="font-size:8px;color:var(--muted)">No active tasks</div>';
    // Per-agent tasks (show category match or just most recent)
    ANT_AGENTS.forEach(agent=>{
      const el=document.getElementById('ant-'+agent.id+'-tasks');
      if(!el) return;
      const agTasks=tasks.filter(t=>t.category===agent.id&&t.status!=='done').slice(0,2);
      el.innerHTML=agTasks.length?agTasks.map(t=>`<div style="font-size:8px;padding:2px 6px;border-left:2px solid ${agent.color};color:${agent.color};background:${agent.color}11">${esc(t.title.slice(0,36))}</div>`).join(''):'<div style="font-size:8px;color:var(--muted)">Idle</div>';
    });
  }catch(e){}
}

// ─── CALENDAR MODAL ───────────────────────────────────────────────────────────
let _calViewDate=new Date(), _calSelDate=new Date(), _calEvents=[], _calAdvisedEvents=[];
let _calCtxTarget=null; // {type:'empty'|'advised', hour, event}

async function loadCalendarModal(body){
  body.style.padding='0'; body.style.overflow='hidden';
  _calViewDate=new Date(); _calSelDate=new Date();
  // Fetch events
  try{ const r=await fetch('/api/specialist/vision/events?hours=720').then(r=>r.json()); _calEvents=r.events||[]; }catch(e){_calEvents=[];}
  // Demo advised events
  _calAdvisedEvents=[
    {title:'Review project timeline', time:'10:00', duration:60, date:new Date().toDateString(), advised:true},
    {title:'Team sync call', time:'14:30', duration:30, date:new Date().toDateString(), advised:true},
  ];
  body.innerHTML=`<div class="cal-layout">
    <div class="cal-mini">
      <div class="cal-mini-header">
        <button class="cal-nav-btn" onclick="calPrevMonth()">‹</button>
        <div class="cal-mini-title" id="cal-mini-title"></div>
        <button class="cal-nav-btn" onclick="calNextMonth()">›</button>
      </div>
      <div class="cal-grid" id="cal-mini-grid"></div>
    </div>
    <div class="cal-day-view">
      <div class="cal-day-header">
        <div class="cal-day-title" id="cal-day-title"></div>
        <button class="cal-approve-btn" onclick="calApproveAll()">✓ APPROVE ALL JARVIS ADVICE</button>
      </div>
      <div class="cal-scroll" id="cal-day-scroll" oncontextmenu="calRightClick(event,null,null)"></div>
    </div>
  </div>`;
  _renderCalMini();
  _renderDayView();
}

function _renderCalMini(){
  const y=_calViewDate.getFullYear(), m=_calViewDate.getMonth();
  const months=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  document.getElementById('cal-mini-title').textContent=months[m]+' '+y;
  const grid=document.getElementById('cal-mini-grid');
  if(!grid) return;
  const dows=['M','T','W','T','F','S','S'];
  const first=new Date(y,m,1),lastDay=new Date(y,m+1,0).getDate();
  let startDow=(first.getDay()+6)%7; // Monday=0
  let html=dows.map(d=>`<div class="cal-dow">${d}</div>`).join('');
  for(let i=0;i<startDow;i++) html+='<div></div>';
  const todayStr=new Date().toDateString();
  for(let d=1;d<=lastDay;d++){
    const dateObj=new Date(y,m,d);
    const dStr=dateObj.toDateString();
    const isToday=dStr===todayStr;
    const isSel=dStr===_calSelDate.toDateString();
    const hasEvt=_calEvents.some(e=>{const es=e.start?new Date(e.start):null; return es&&es.toDateString()===dStr;});
    html+=`<div class="cal-day${isToday?' today':''}${isSel?' selected':''}${hasEvt?' has-events':''}" onclick="calSelectDay(${y},${m},${d})">${d}</div>`;
  }
  grid.innerHTML=html;
}

function calSelectDay(y,m,d){ _calSelDate=new Date(y,m,d); _renderCalMini(); _renderDayView(); }
function calPrevMonth(){ _calViewDate=new Date(_calViewDate.getFullYear(),_calViewDate.getMonth()-1,1); _renderCalMini(); }
function calNextMonth(){ _calViewDate=new Date(_calViewDate.getFullYear(),_calViewDate.getMonth()+1,1); _renderCalMini(); }

function _renderDayView(){
  const title=document.getElementById('cal-day-title');
  if(title){
    const opts={weekday:'long',day:'numeric',month:'long',year:'numeric'};
    title.textContent=_calSelDate.toLocaleDateString('en-GB',opts).toUpperCase();
  }
  const scroll=document.getElementById('cal-day-scroll');
  if(!scroll) return;
  const selStr=_calSelDate.toDateString();
  // Get events for selected day
  const dayEvts=_calEvents.filter(e=>{ const es=e.start?new Date(e.start):null; return es&&es.toDateString()===selStr; });
  const advisedDay=_calAdvisedEvents.filter(e=>e.date===selStr);
  let html='';
  for(let h=6;h<23;h++){
    const label=h===12?'12 PM':h<12?h+' AM':(h-12)+' PM';
    // Find events starting in this hour
    const hEvts=dayEvts.filter(e=>{ const es=e.start?new Date(e.start):null; return es&&es.getHours()===h; });
    const hAdv=advisedDay.filter(e=>{ const parts=e.time.split(':'); return parseInt(parts[0])===h; });
    let evtBlocks='';
    hEvts.forEach((e,i)=>{
      const mins=e.start?new Date(e.start).getMinutes():0;
      const dur=e.end&&e.start?(new Date(e.end)-new Date(e.start))/60000:60;
      const top=Math.round(mins/60*52),height=Math.max(20,Math.round(dur/60*52));
      evtBlocks+=`<div class="cal-event-block normal" style="top:${top}px;height:${height}px" oncontextmenu="calRightClick(event,null,'${esc(e.title||'')}')">${esc(e.title||'Event')}</div>`;
    });
    hAdv.forEach((e,i)=>{
      const parts=e.time.split(':'); const mins=parseInt(parts[1]||0);
      const top=Math.round(mins/60*52),height=Math.max(20,Math.round((e.duration||60)/60*52));
      evtBlocks+=`<div class="cal-event-block advised" style="top:${top}px;height:${height}px" oncontextmenu="calRightClick(event,'advised','${esc(e.title)}')" title="JARVIS suggests: right-click to accept">◈ ${esc(e.title)}</div>`;
    });
    html+=`<div class="cal-hour-row">
      <div class="cal-hour-label">${label}</div>
      <div class="cal-hour-slot" data-hour="${h}" oncontextmenu="calRightClick(event,'empty',null,${h})">${evtBlocks}</div>
    </div>`;
  }
  scroll.innerHTML=html;
}

let _calCtxAdvisedTitle='', _calCtxHour=0;
function calRightClick(e,type,evtTitle,hour){
  e.preventDefault(); e.stopPropagation();
  hideCalCtx();
  _calCtxHour=hour||0; _calCtxAdvisedTitle=evtTitle||'';
  const menu=document.getElementById('cal-ctx');
  const acceptItem=document.getElementById('cal-ctx-accept');
  if(type==='advised'&&acceptItem){ acceptItem.style.display=''; acceptItem.textContent='✓ Accept: '+evtTitle.slice(0,24); }
  else if(acceptItem) acceptItem.style.display='none';
  menu.style.display='block';
  menu.style.left=Math.min(e.clientX, window.innerWidth-180)+'px';
  menu.style.top=Math.min(e.clientY, window.innerHeight-100)+'px';
}
function hideCalCtx(){ const m=document.getElementById('cal-ctx'); if(m) m.style.display='none'; }
document.addEventListener('click',()=>hideCalCtx());
function calCtxNewEvent(){
  hideCalCtx();
  const popup=document.getElementById('cal-event-popup');
  if(!popup) return;
  popup.style.display='block';
  // Position to the left of the modal
  const modal=document.getElementById('modal-win');
  const mRect=modal?modal.getBoundingClientRect():null;
  if(mRect){ popup.style.left=Math.max(8,mRect.left-310)+'px'; popup.style.top=(mRect.top+60)+'px'; }
  else{ popup.style.left='20px'; popup.style.top='100px'; }
  if(_calCtxHour){ const h=_calCtxHour; document.getElementById('cep-time').value=(h<10?'0'+h:h)+':00'; }
  setTimeout(()=>document.getElementById('cep-name')?.focus(),50);
}
function calCtxAccept(){
  hideCalCtx();
  // Move advised event to real calendar (send to JARVIS)
  if(ws&&ws.readyState===1) ws.send(`Accept the calendar suggestion for "${_calCtxAdvisedTitle}" on ${_calSelDate.toDateString()}`);
  // Remove from advised list
  _calAdvisedEvents=_calAdvisedEvents.filter(e=>e.title!==_calCtxAdvisedTitle);
  _renderDayView();
}
function calApproveAll(){
  const selStr=_calSelDate.toDateString();
  const toAccept=_calAdvisedEvents.filter(e=>e.date===selStr);
  if(toAccept.length===0){alert('No JARVIS suggestions for this day.');return;}
  toAccept.forEach(e=>{ if(ws&&ws.readyState===1) ws.send(`Accept calendar suggestion: "${e.title}" on ${selStr}`); });
  _calAdvisedEvents=_calAdvisedEvents.filter(e=>e.date!==selStr);
  _renderDayView();
}
function closeCepPopup(){ const p=document.getElementById('cal-event-popup'); if(p) p.style.display='none'; }
async function submitCepEvent(){
  const name=document.getElementById('cep-name').value.trim();
  if(!name) return;
  const time=document.getElementById('cep-time').value;
  const cat=document.getElementById('cep-cat').value;
  const loc=document.getElementById('cep-location').value.trim();
  const flagged=document.getElementById('cep-flag').checked;
  const dateStr=_calSelDate.toDateString();
  if(ws&&ws.readyState===1){
    const msg=`Add a ${cat} calendar event: "${name}"${loc?' at '+loc:''} on ${dateStr}${time?' at '+time:''}${flagged?' — please advise me on this event':''}`;
    ws.send(msg);
  }
  closeCepPopup();
  document.getElementById('cep-name').value=''; document.getElementById('cep-location').value=''; document.getElementById('cep-flag').checked=false;
  setTimeout(_renderDayView,2000);
}

// ─── INBOX MODAL ──────────────────────────────────────────────────────────────
async function loadInboxModal(body){
  const d=await(await fetch('/api/status')).json();
  const unread=d.unread||0;
  let emails=[];
  try{ const mem=await(await fetch('/api/memory')).json(); const ef=mem.facts.find(f=>f.key==='gmail_emails'); if(ef) emails=JSON.parse(ef.value)||[]; }catch(e){}
  const impClass=(imp)=>imp>.7?'imp-high':imp>.4?'imp-med':'imp-low';
  const badge=(imp)=>imp>.7?'<span class="email-badge badge-high">HIGH</span>':imp>.4?'<span class="email-badge badge-med">MED</span>':'<span class="email-badge badge-low">LOW</span>';
  body.innerHTML=`<div style="margin-bottom:16px;font-size:10px;color:var(--muted)">${unread} UNREAD — ranked by importance</div>
    ${emails.length?emails.map((e,i)=>{const imp=e.importance||e.score||(i<3?.8:i<7?.5:.2);return`<div class="email-item ${impClass(imp)}"><div><div class="email-subject">${esc(e.subject||'(no subject)')}</div><div class="email-from">${esc(e.from||e.sender||'Unknown')}</div></div>${badge(imp)}</div>`;}).join(''):`<div class="empty">${unread>0?unread+' unread (Gmail OAuth required for full list)':'No emails'}</div>`}`;
}

// ─── BRAIN MODAL ──────────────────────────────────────────────────────────────
let _brainTab='today';
// Cached HD items and today's history for cross-linking
let _hdItems=[], _todayHistory=[], _hdHighlightId=null;

async function loadBrainModal(body){
  body.style.cssText='display:flex;flex-direction:column;height:100%;padding:0;overflow:hidden';
  body.innerHTML=`
    <div class="brain-tabs" style="flex-shrink:0;padding:0 20px">
      <button class="brain-tab-btn active" onclick="switchBrainTab('today',this)">TODAY'S MEMORY</button>
      <button class="brain-tab-btn" onclick="switchBrainTab('hardrive',this)">HARD DRIVE</button>
    </div>
    <div id="brain-content" style="flex:1;position:relative;overflow:hidden"></div>`;
  // Pre-load both data sets so cross-links work
  await _fetchBrainData();
  switchBrainTab('today', body.querySelector('.brain-tab-btn.active'));
}

async function _fetchBrainData(){
  try{
    const [memRes, hdRes] = await Promise.all([
      fetch('/api/memory').then(r=>r.json()),
      fetch('/api/brain/hardrive').then(r=>r.json())
    ]);
    _hdItems = hdRes.items || [];
    const today = new Date().toDateString();
    _todayHistory = (memRes.history||[]).filter(h=>{
      if(!h.role||!h.content) return false;
      const ts=h.ts||h.timestamp||'';
      if(!ts) return true;
      try{ return new Date(ts).toDateString()===today; }catch(e){ return true; }
    }).slice(-40);
  }catch(e){ _hdItems=[]; _todayHistory=[]; }
}

async function switchBrainTab(tab, btn){
  document.querySelectorAll('.brain-tab-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  _brainTab=tab;
  const content=document.getElementById('brain-content');
  if(!content) return;
  if(tab==='today') _drawTodaySpider(content);
  else _loadHardDrive(content);
}

// ─── TODAY'S MEMORY SPIDER ────────────────────────────────────────────────────
// Stop words for keyword extraction
const _SW=new Set('i the a an is are was were have has be been to of and or in on at it its this that you me we my your what when how can could would should will do does did for with as by from but not no yes so if then just about up out get got know said tell told ask asked going goes say let know think'.split(' '));

function _extractKW(text){
  return [...new Set(text.toLowerCase().split(/\W+/).filter(w=>w.length>4&&!_SW.has(w)))].slice(0,8);
}

function _textOf(h){
  return typeof h.content==='string'?h.content:(Array.isArray(h.content)?h.content.map(c=>c.text||'').join(' '):'');
}

function _drawTodaySpider(content){
  content.innerHTML='';
  if(!_todayHistory.length){
    content.innerHTML=`<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:12px"><div style="font-size:40px;opacity:.15">🧠</div><div style="font-size:10px;color:var(--muted);letter-spacing:2px">NO CONVERSATION TODAY YET</div></div>`;
    return;
  }
  content.innerHTML=`
    <canvas id="today-canvas" style="width:100%;height:100%"></canvas>
    <div id="today-tip" style="position:absolute;background:var(--bg2);border:1px solid var(--c1);padding:8px 12px;font-size:10px;pointer-events:none;display:none;color:var(--text);border-radius:2px;max-width:300px;z-index:10;line-height:1.6"></div>
    <div id="today-legend" style="position:absolute;bottom:10px;left:12px;display:flex;flex-direction:column;gap:5px;z-index:5">
      <div style="font-size:8px;color:var(--muted);letter-spacing:1px;margin-bottom:2px">LEGEND</div>
      <div style="display:flex;align-items:center;gap:6px"><div style="width:16px;height:1px;background:rgba(0,212,255,.5)"></div><span style="font-size:8px;color:var(--muted)">conversation flow</span></div>
      <div style="display:flex;align-items:center;gap:6px"><div style="width:16px;height:1px;background:rgba(255,150,50,.6);border-top:1px dashed rgba(255,150,50,.6)"></div><span style="font-size:8px;color:var(--muted)">topic link</span></div>
      <div style="display:flex;align-items:center;gap:6px"><div style="width:16px;height:1px;background:#ffd700;border-top:1px dashed #ffd70066"></div><span style="font-size:8px;color:var(--muted)">→ hard drive</span></div>
    </div>`;

  setTimeout(()=>{
    const canvas=document.getElementById('today-canvas');
    const tip=document.getElementById('today-tip');
    if(!canvas) return;
    canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight;
    const W=canvas.width, H=canvas.height, cx=W/2, cy=H/2;
    if(!W||!H) return;

    const msgs=_todayHistory;
    const N=msgs.length;
    const nodes=[];
    const edges=[];

    // ── Center node ────────────────────────────────────────────────────────────
    nodes.push({id:'c',label:'TODAY',x:cx,y:cy,r:24,color:'#00d4ff',
      type:'center',text:'Today\'s conversation',kw:[]});

    // ── Cluster messages by topic keyword ──────────────────────────────────────
    // Group into up to 6 topic branches radiating from center
    const topicMap={};  // keyword → [msgIdx, ...]
    const allKW=[];
    msgs.forEach((h,i)=>{
      const kw=_extractKW(_textOf(h));
      allKW.push(kw);
      kw.forEach(w=>{ if(!topicMap[w]) topicMap[w]=[]; topicMap[w].push(i); });
    });
    // Pick top branches: keywords shared by multiple messages
    const branches=Object.entries(topicMap)
      .filter(([,v])=>v.length>=2)
      .sort((a,b)=>b[1].length-a[1].length)
      .slice(0,6)
      .map(([kw,idxs])=>({kw,idxs}));
    const branchAngles=branches.map((_,i)=>
      (i/Math.max(branches.length,1))*Math.PI*2 - Math.PI/2
    );
    const branchR=Math.min(cx,cy)*.38;
    const branchNodes={};  // kw → nodeId

    // Add branch hub nodes
    branches.forEach((b,i)=>{
      const bx=cx+Math.cos(branchAngles[i])*branchR;
      const by=cy+Math.sin(branchAngles[i])*branchR;
      const bid='b'+i;
      branchNodes[b.kw]=bid;
      nodes.push({id:bid,label:b.kw.slice(0,12),x:bx,y:by,r:13,
        color:'rgba(255,150,50,.9)',type:'branch',text:`Topic: ${b.kw} (${b.idxs.length} messages)`,kw:[b.kw]});
      edges.push({a:'c',b:bid,type:'branch'});
    });

    // ── Per-message nodes ──────────────────────────────────────────────────────
    // Track which branch each message belongs to (first strong match)
    const msgBranch=new Array(N).fill(null);
    branches.forEach((b,bi)=>{
      b.idxs.forEach(mi=>{if(msgBranch[mi]===null) msgBranch[mi]=bi;});
    });

    const branchPlaced={};  // bid → count placed
    branches.forEach(b=>{ branchPlaced[branchNodes[b.kw]]=0; });

    msgs.forEach((h,i)=>{
      const isUser=h.role==='user';
      const text=_textOf(h);
      const kw=allKW[i];
      const ts=h.ts||h.timestamp||'';
      let timeStr='';
      try{const d=new Date(ts);if(!isNaN(d))timeStr=d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}catch(e){}

      // Position: near its branch hub, or in outer ring if unmatched
      let x,y;
      const bi=msgBranch[i];
      if(bi!==null){
        const bNode=nodes.find(n=>n.id===('b'+bi));
        const placed=branchPlaced['b'+bi]||0;
        branchPlaced['b'+bi]=placed+1;
        const spreadAngle=branchAngles[bi]+(placed%2===0?1:-1)*(placed+1)*0.28;
        const dist=50+placed*22;
        x=bNode.x+Math.cos(spreadAngle)*dist;
        y=bNode.y+Math.sin(spreadAngle)*dist;
      } else {
        // No branch — place in outer ring
        const angle=(i/N)*Math.PI*2 - Math.PI/2;
        const r=Math.min(cx,cy)*.75;
        x=cx+Math.cos(angle)*r;
        y=cy+Math.sin(angle)*r;
        // Light radial edge to center for unmatched
        edges.push({a:'c',b:'m'+i,type:'radial'});
      }
      x=Math.max(14,Math.min(W-14,x));
      y=Math.max(14,Math.min(H-14,y));

      // HD cross-link
      const hdLink=_hdItems.find(it=>kw.some(w=>
        it.title.toLowerCase().includes(w)||it.content.toLowerCase().includes(w)));

      nodes.push({id:'m'+i,label:timeStr||('#'+(i+1)),x,y,
        r:isUser?7:10,
        color:isUser?'rgba(160,210,230,.85)':'#00d4ff',
        type:isUser?'user':'jarvis',
        text:text.slice(0,180),kw,hdLink:hdLink||null,timeStr,role:h.role});

      // Edge from branch or direct radial
      if(bi!==null){
        edges.push({a:'b'+bi,b:'m'+i,type:'branch-leaf'});
      }
    });

    // ── Temporal chain between consecutive messages ────────────────────────────
    for(let i=1;i<N;i++) edges.push({a:'m'+(i-1),b:'m'+i,type:'temporal'});

    // ── HD cross-link edges ────────────────────────────────────────────────────
    // Draw gold dashed line from HD-linked msg node toward edge of canvas
    // (indicating it's stored in Hard Drive)
    nodes.filter(n=>n.hdLink).forEach(n=>{
      edges.push({a:n.id,b:'__hd__'+n.id,type:'hd_link',node:n});
    });

    // ── Float animation ────────────────────────────────────────────────────────
    const floats=nodes.map(()=>({ox:0,oy:0,vx:(Math.random()-.5)*.18,vy:(Math.random()-.5)*.18}));
    let hoveredNode=null;

    function draw(){
      if(!document.getElementById('today-canvas')) return;
      requestAnimationFrame(draw);
      const ctx=canvas.getContext('2d');
      ctx.clearRect(0,0,W,H);

      // Float
      floats.forEach((f,i)=>{
        if(nodes[i].type==='center') return;
        f.ox+=f.vx; f.oy+=f.vy;
        if(Math.abs(f.ox)>4)f.vx*=-1;
        if(Math.abs(f.oy)>4)f.vy*=-1;
      });

      const np=(id)=>{
        const idx=nodes.findIndex(n=>n.id===id);
        if(idx<0) return null;
        return {x:nodes[idx].x+floats[idx].ox, y:nodes[idx].y+floats[idx].oy, n:nodes[idx]};
      };

      // ── Draw edges ──────────────────────────────────────────────────────────
      edges.forEach(e=>{
        if(e.type==='hd_link'){
          // Gold dashed arrow from node toward right edge (HD indicator)
          const p=np(e.a); if(!p) return;
          const tgtX=Math.min(p.x+55,W-10), tgtY=p.y-20;
          ctx.save();
          ctx.strokeStyle='rgba(255,215,0,.55)'; ctx.lineWidth=1; ctx.setLineDash([3,4]);
          ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(tgtX,tgtY); ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle='rgba(255,215,0,.7)'; ctx.font='8px serif';
          ctx.fillText('💾',tgtX,tgtY+4);
          ctx.restore();
          return;
        }
        const a=np(e.a), b=np(e.b); if(!a||!b) return;
        ctx.save();
        if(e.type==='branch'){
          ctx.strokeStyle='rgba(255,150,50,.25)'; ctx.lineWidth=1.5; ctx.setLineDash([]);
        } else if(e.type==='branch-leaf'){
          ctx.strokeStyle='rgba(255,150,50,.18)'; ctx.lineWidth=1; ctx.setLineDash([2,4]);
        } else if(e.type==='temporal'){
          ctx.strokeStyle='rgba(0,212,255,.22)'; ctx.lineWidth=.8; ctx.setLineDash([]);
        } else { // radial
          ctx.strokeStyle='rgba(0,120,170,.12)'; ctx.lineWidth=.5; ctx.setLineDash([3,6]);
        }
        ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
      });

      // ── Draw nodes ──────────────────────────────────────────────────────────
      nodes.forEach((n,i)=>{
        const nx=nodes[i].x+floats[i].ox, ny=nodes[i].y+floats[i].oy;
        const isH=hoveredNode===n;
        ctx.save();
        if(n.type==='center'||n.type==='branch'||n.type==='jarvis'||isH){
          ctx.shadowColor=n.color; ctx.shadowBlur=isH?22:8;
        }
        ctx.beginPath(); ctx.arc(nx,ny,n.r+(isH?3:0),0,Math.PI*2);
        const fills={center:'rgba(0,212,255,.15)',branch:'rgba(255,150,50,.12)',
          user:'rgba(18,36,55,.95)',jarvis:'rgba(0,40,60,.95)'};
        ctx.fillStyle=fills[n.type]||'rgba(10,30,50,.9)'; ctx.fill();
        ctx.strokeStyle=isH?'#fff':n.color; ctx.lineWidth=isH?2:1.5; ctx.stroke();
        ctx.shadowBlur=0;

        // Label
        ctx.fillStyle=n.type==='center'?'#00d4ff':n.type==='branch'?'rgba(255,170,60,.9)':
          n.type==='user'?'rgba(160,210,230,.8)':'#00d4ff';
        const fs=n.type==='center'?11:n.type==='branch'?8:7;
        ctx.font=`${fs}px Courier New`; ctx.textAlign='center';
        const labelY=n.type==='center'||n.type==='branch'? ny+4 : ny+n.r+10;
        ctx.fillText(n.label.slice(0,14),nx,labelY);

        // HD link badge 💾
        if(n.hdLink){
          ctx.font='9px serif';
          ctx.fillText('💾',nx+n.r+1,ny-n.r);
        }
        ctx.restore();
      });
    }
    draw();

    // ── Hover + click ─────────────────────────────────────────────────────────
    canvas.addEventListener('mousemove',ev=>{
      const rect=canvas.getBoundingClientRect(),mx=ev.clientX-rect.left,my=ev.clientY-rect.top;
      hoveredNode=null;
      nodes.forEach((n,i)=>{
        const nx=nodes[i].x+floats[i].ox, ny=nodes[i].y+floats[i].oy;
        if(Math.sqrt((mx-nx)**2+(my-ny)**2)<=n.r+7) hoveredNode=n;
      });
      if(hoveredNode&&hoveredNode.type!=='center'){
        const tipX=Math.min(ev.clientX-rect.left+16,W-310);
        const tipY=Math.max(6,ev.clientY-rect.top-70);
        tip.style.left=tipX+'px'; tip.style.top=tipY+'px'; tip.style.display='block';
        const roleLabel=hoveredNode.type==='user'?'YOU':hoveredNode.type==='branch'?'TOPIC':'JARVIS';
        const roleColor=hoveredNode.type==='user'?'var(--muted)':hoveredNode.type==='branch'?'rgba(255,150,50,.9)':'var(--c1)';
        const hdHtml=hoveredNode.hdLink
          ? `<div style="margin-top:7px;padding-top:6px;border-top:1px solid var(--border);color:#ffd700;font-size:8px;letter-spacing:1px">💾 LINKED TO HARD DRIVE<br><em style="color:var(--text)">${esc(hoveredNode.hdLink.title)}</em><br><span style="color:var(--muted)">${esc((hoveredNode.hdLink.content||'').slice(0,80))}</span></div>`
          : '';
        const kwHtml=hoveredNode.kw&&hoveredNode.kw.length
          ? `<div style="margin-top:5px;color:rgba(255,150,50,.7);font-size:8px">${hoveredNode.kw.slice(0,5).join(' · ')}</div>`
          : '';
        tip.innerHTML=`<div style="font-size:8px;color:${roleColor};letter-spacing:1px;margin-bottom:4px">${roleLabel}${hoveredNode.timeStr?' · '+hoveredNode.timeStr:''}</div>${esc(hoveredNode.text.slice(0,160))}${kwHtml}${hdHtml}
          ${hoveredNode.hdLink?'<div style="margin-top:6px;font-size:8px;color:rgba(255,215,0,.6);letter-spacing:1px">click → view in hard drive</div>':''}`;
        canvas.style.cursor=hoveredNode.hdLink?'pointer':'default';
      } else { tip.style.display='none'; canvas.style.cursor='default'; }
    });
    canvas.addEventListener('mouseleave',()=>{tip.style.display='none';hoveredNode=null;});
    canvas.addEventListener('click',()=>{
      if(hoveredNode&&hoveredNode.hdLink){
        _hdHighlightId=hoveredNode.hdLink.id;
        const tabBtn=document.querySelector('.brain-tab-btn:nth-child(2)');
        switchBrainTab('hardrive',tabBtn);
      }
    });
  }, 80);
}

// ─── HARD DRIVE ────────────────────────────────────────────────────────────────
let _hdTab='info';
async function _loadHardDrive(content){
  if(_hdItems.length===0){
    try{ const r=await fetch('/api/brain/hardrive').then(r=>r.json()); _hdItems=r.items||[]; }catch(e){}
  }
  content.innerHTML=`<div class="hd-layout" style="height:100%">
    <div class="hd-tabs">
      <button class="hd-tab-btn active" onclick="switchHDTab('info',this)">ℹ️ INFO</button>
      <button class="hd-tab-btn" onclick="switchHDTab('memories',this)">💭 MEMORIES</button>
      <button class="hd-tab-btn" onclick="switchHDTab('goals',this)">🎯 GOALS</button>
      <button class="hd-tab-btn" onclick="switchHDTab('relations',this)">🔗 RELATIONS</button>
    </div>
    <div class="hd-canvas-wrap">
      <canvas id="hd-canvas"></canvas>
      <div id="hd-tooltip"></div>
    </div>
  </div>`;
  setTimeout(()=>switchHDTab('info', content.querySelector('.hd-tab-btn.active')), 40);
}

async function switchHDTab(tab, btn){
  document.querySelectorAll('.hd-tab-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  _hdTab=tab;
  if(_hdItems.length===0) try{ const r=await fetch('/api/brain/hardrive').then(r=>r.json()); _hdItems=r.items||[]; }catch(e){}
  _drawHDGraph(tab);
}

function _drawHDGraph(tab){
  const canvas=document.getElementById('hd-canvas');
  const tip=document.getElementById('hd-tooltip');
  if(!canvas) return;
  if(!canvas.offsetWidth){ setTimeout(()=>_drawHDGraph(tab),60); return; }
  canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight;
  const W=canvas.width, H=canvas.height, cx=W/2, cy=H/2;
  if(!W||!H) return;

  const tabColors={info:'#00d4ff',memories:'#aa66ff',goals:'#00ff88',relations:'#ff8844'};
  const color=tabColors[tab]||'#00d4ff';
  const tabItems=_hdItems.filter(it=>it.tab===tab);

  const nodes=[];
  nodes.push({id:'core',label:'JARVIS\nHARD DRIVE',x:cx,y:cy,r:24,color:color,
    type:'core',text:`${tab.toUpperCase()} — ${tabItems.length} item${tabItems.length!==1?'s':''}`});

  if(tabItems.length===0){
    nodes.push({id:'empty',label:'Empty',x:cx,y:cy-120,r:12,color:'rgba(58,106,128,.5)',
      type:'empty',text:'JARVIS will save important facts here automatically.',parent:'core'});
  } else {
    // Group by first tag for sub-clusters
    const groups={};
    tabItems.forEach(it=>{
      const tag=(it.tags&&it.tags[0])||'general';
      if(!groups[tag]) groups[tag]=[];
      groups[tag].push(it);
    });
    const groupKeys=Object.keys(groups);
    const innerR=Math.min(W,H)*.24;
    const itemR=Math.min(W,H)*.14;

    groupKeys.forEach((tag,gi)=>{
      const ga=(gi/Math.max(groupKeys.length,1))*Math.PI*2-Math.PI/2;
      const gx=cx+Math.cos(ga)*innerR, gy=cy+Math.sin(ga)*innerR;
      const gid='g_'+gi;
      nodes.push({id:gid,label:tag.replace(/_/g,' ').slice(0,14),x:gx,y:gy,r:14,
        color:color,type:'group',text:`${groups[tag].length} item${groups[tag].length!==1?'s':''} · ${tag}`,parent:'core'});

      groups[tag].forEach((it,ii)=>{
        const itemCount=groups[tag].length;
        const ia=ga+(ii-(itemCount-1)/2)*0.55;
        const ix=gx+Math.cos(ia)*itemR, iy=gy+Math.sin(ia)*itemR;
        const kw=_extractKW(it.title+' '+it.content);
        const todayLink=_todayHistory.find(h=>kw.some(w=>_textOf(h).toLowerCase().includes(w)));
        // Is this the highlighted node from today's spider click?
        const isHighlighted=_hdHighlightId!=null && it.id===_hdHighlightId;
        nodes.push({
          id:'it_'+it.id, label:it.title.slice(0,16),
          x:Math.max(14,Math.min(W-14,ix)), y:Math.max(14,Math.min(H-14,iy)),
          r:isHighlighted?13:9, color:isHighlighted?'#ffd700':color,
          type:'item', text:it.content, parent:gid,
          source:it.source||'', todayLink:!!todayLink, highlighted:isHighlighted,
          rawItem:it
        });
      });
    });
  }

  const floats=nodes.map(()=>({ox:0,oy:0,vx:(Math.random()-.5)*.18,vy:(Math.random()-.5)*.18}));
  let hoveredNode=null;

  // Auto-pulse the highlighted node for a few seconds then clear
  let _hlPulse=_hdHighlightId!=null?30:0;
  if(_hdHighlightId) setTimeout(()=>{ _hdHighlightId=null; },4000);

  function draw(){
    if(!document.getElementById('hd-canvas')) return;
    requestAnimationFrame(draw);
    const ctx=canvas.getContext('2d');
    ctx.clearRect(0,0,W,H);
    floats.forEach((f,i)=>{
      if(nodes[i].type==='core') return;
      f.ox+=f.vx; f.oy+=f.vy;
      if(Math.abs(f.ox)>6)f.vx*=-1; if(Math.abs(f.oy)>6)f.vy*=-1;
    });

    // Edges
    nodes.forEach((n,i)=>{
      if(!n.parent) return;
      const p=nodes.find(x=>x.id===n.parent); if(!p) return;
      const pi=nodes.indexOf(p);
      const nx=n.x+floats[i].ox, ny=n.y+floats[i].oy;
      const px=p.x+floats[pi].ox, py=p.y+floats[pi].oy;
      ctx.save();
      ctx.beginPath(); ctx.moveTo(px,py); ctx.lineTo(nx,ny);
      ctx.strokeStyle=n.highlighted?'rgba(255,215,0,.4)':`${color}33`;
      ctx.lineWidth=n.type==='group'?1.5:n.highlighted?1.5:0.8;
      if(n.highlighted) ctx.setLineDash([]);
      ctx.stroke(); ctx.setLineDash([]); ctx.restore();
    });

    // Nodes
    nodes.forEach((n,i)=>{
      const nx=n.x+floats[i].ox, ny=n.y+floats[i].oy;
      const isH=hoveredNode===n;
      const isHL=n.highlighted;
      ctx.save();
      if(n.type==='core'||isH||isHL){
        ctx.shadowColor=isHL?'#ffd700':n.color;
        ctx.shadowBlur=isHL?(_hlPulse>0?24:14):isH?20:10;
      }
      if(_hlPulse>0) _hlPulse--;
      ctx.beginPath(); ctx.arc(nx,ny,n.r+(isH?3:isHL?2:0),0,Math.PI*2);
      ctx.fillStyle=n.type==='core'?`${color}1a`:isHL?'rgba(255,215,0,.15)':'rgba(4,28,44,.92)';
      ctx.fill();
      ctx.strokeStyle=isH?'#fff':isHL?'#ffd700':n.color;
      ctx.lineWidth=isH||isHL?2:1.2; ctx.stroke();
      ctx.shadowBlur=0;

      // Label
      ctx.fillStyle=n.type==='core'?color:n.type==='group'?'rgba(210,235,245,.9)':
        isHL?'#ffd700':'rgba(180,210,230,.65)';
      ctx.font=`${n.type==='core'?10:n.type==='group'?9:8}px Courier New`;
      ctx.textAlign='center';
      if(n.r>8||isH){
        const lines=n.label.split('\n');
        lines.forEach((line,li)=>ctx.fillText(line.slice(0,16),nx,ny+n.r+10+li*11));
      }
      if(n.todayLink){ ctx.font='9px serif'; ctx.fillText('📍',nx+n.r+1,ny-n.r+1); }
      if(isHL){ ctx.font='9px serif'; ctx.fillText('★',nx-n.r-1,ny-n.r+1); }
      ctx.restore();
    });
  }
  draw();

  if(tip){
    canvas.addEventListener('mousemove',e=>{
      const rect=canvas.getBoundingClientRect(),mx=e.clientX-rect.left,my=e.clientY-rect.top;
      hoveredNode=null;
      nodes.forEach((n,i)=>{
        const nx=n.x+floats[i].ox, ny=n.y+floats[i].oy;
        if(Math.sqrt((mx-nx)**2+(my-ny)**2)<=n.r+6) hoveredNode=n;
      });
      if(hoveredNode&&hoveredNode.type!=='core'){
        tip.style.display='block';
        tip.style.left=Math.min(mx+14,W-240)+'px';
        tip.style.top=Math.max(4,my-55)+'px';
        const todayTxt=hoveredNode.todayLink
          ?`<div style="margin-top:6px;color:#00ff88;font-size:8px;letter-spacing:1px">📍 IN TODAY'S CONVERSATION — click to jump</div>`:'';
        const srcTxt=hoveredNode.source
          ?`<div style="margin-top:3px;color:var(--muted);font-size:8px">saved by: ${esc(hoveredNode.source)}</div>`:'';
        tip.innerHTML=`<strong style="color:${hoveredNode.highlighted?'#ffd700':color}">${esc(hoveredNode.label)}</strong>
          <div style="color:var(--text);font-size:9px;margin-top:4px;line-height:1.5">${esc(hoveredNode.text.slice(0,140))}</div>
          ${srcTxt}${todayTxt}`;
        canvas.style.cursor=hoveredNode.todayLink?'pointer':'default';
      } else { tip.style.display='none'; canvas.style.cursor='default'; }
    });
    canvas.addEventListener('mouseleave',()=>{tip.style.display='none';hoveredNode=null;});
    canvas.addEventListener('click',()=>{
      if(hoveredNode&&hoveredNode.todayLink){
        const btn=document.querySelector('.brain-tab-btn');
        switchBrainTab('today',btn);
      }
    });
  }
}

// ─── ROBOT MODAL (Detailed agent view) ────────────────────────────────────────
function loadRobotModal(body){
  body.style.cssText='padding:16px 20px;overflow:hidden;height:100%;display:flex;gap:16px';
  const agents=[
    {id:'jarvis', name:'JARVIS', color:'#00d4ff', desc:'Central orchestrator', progress:100, thought:'💭', tools:'memory, voice, tasks, calendar', status:'ACTIVE'},
    {id:'ultron', name:'ULTRON', color:'#cc0000', desc:'Security & threat intelligence', progress:72, thought:'🛡️', tools:'breach-check, port-scan, watchlist', status:'SCANNING'},
    {id:'vision', name:'VISION', color:'#00cc66', desc:'Intelligence & planning', progress:55, thought:'👁️', tools:'calendar, plans, briefings', status:'PLANNING'},
    {id:'friday', name:'FRIDAY', color:'#4488ff', desc:'Content & research', progress:30, thought:'📰', tools:'news-api, blog-gen, newspaper', status:'IDLE'},
    {id:'gresz',  name:'GRESZ',  color:'#c8a840', desc:'Business intelligence', progress:45, thought:'📊', tools:'projects, pipeline, clients', status:'MONITORING'},
  ];
  body.innerHTML=`
    <div style="flex:1;position:relative;overflow:hidden;min-width:0">
      <canvas id="robot-canvas" style="width:100%;height:100%;display:block"></canvas>
    </div>
    <div style="width:250px;flex-shrink:0;display:flex;flex-direction:column;gap:8px;overflow-y:auto">
      ${agents.map(a=>`
        <div class="rbot-card ${a.id==='jarvis'?'active':''}" style="border-color:${a.id==='jarvis'?a.color:'var(--border)'}">
          <div class="rbot-name" style="color:${a.color}">${a.thought} ${a.name}</div>
          <div class="rbot-desc">${a.desc}</div>
          <div class="rbot-progress"><div class="rbot-fill" style="width:${a.progress}%;background:${a.color}"></div></div>
          <div class="rbot-tools">${a.tools}</div>
          <div style="font-size:8px;margin-top:4px;color:${a.color}">${a.status}</div>
        </div>`).join('')}
    </div>`;
  // Use setTimeout so the canvas has been laid out before we read its size
  setTimeout(()=>_drawRobotCanvas(agents), 80);
}

// ─── SETTINGS MODAL ───────────────────────────────────────────────────────────
async function loadSettingsModal(body){
  const d=await(await fetch('/api/status')).json();
  const w=d.weather||{};
  body.innerHTML=`
    <div class="profile-hero">
      <div class="profile-avatar">👤</div>
      <div>
        <div class="profile-name">EVAN</div>
        <div class="profile-sub">JARVIS USER · PETERSFIELD, UK</div>
        <div class="profile-sub" style="margin-top:4px;color:var(--green)">● JARVIS ONLINE · ALL SYSTEMS OPERATIONAL</div>
      </div>
    </div>
    <div class="settings-grid">
      <div class="setting-group">
        <div class="sg-title">SYSTEM</div>
        <div class="sg-row"><span class="sg-key">Core</span><span class="sg-val on">ONLINE</span></div>
        <div class="sg-row"><span class="sg-key">Voice</span><span class="sg-val on">BROWSER MIC ACTIVE</span></div>
        <div class="sg-row"><span class="sg-key">WebSocket</span><span class="sg-val on">CONNECTED</span></div>
        <div class="sg-row"><span class="sg-key">Auto-Tasks</span><span class="sg-val on">EVERY 20 MIN</span></div>
      </div>
      <div class="setting-group">
        <div class="sg-title">LOCATION & WEATHER</div>
        <div class="sg-row"><span class="sg-key">City</span><span class="sg-val">Petersfield, UK</span></div>
        <div class="sg-row"><span class="sg-key">Temperature</span><span class="sg-val">${w.temp!==undefined?Math.round(w.temp)+'°C':'—'}</span></div>
        <div class="sg-row"><span class="sg-key">Conditions</span><span class="sg-val">${esc(w.description||w.condition||'—')}</span></div>
        <div class="sg-row"><span class="sg-key">Humidity</span><span class="sg-val">${w.humidity!==undefined?w.humidity+'%':'—'}</span></div>
      </div>
      <div class="setting-group">
        <div class="sg-title">AGENTS</div>
        <div class="sg-row"><span class="sg-key">JARVIS</span><span class="sg-val on">ORCHESTRATOR</span></div>
        <div class="sg-row"><span class="sg-key">ULTRON</span><span class="sg-val on">SECURITY</span></div>
        <div class="sg-row"><span class="sg-key">VISION</span><span class="sg-val on">INTELLIGENCE</span></div>
        <div class="sg-row"><span class="sg-key">FRIDAY</span><span class="sg-val on">CONTENT</span></div>
        <div class="sg-row"><span class="sg-key">GRESZ</span><span class="sg-val on">BUSINESS</span></div>
      </div>
      <div class="setting-group">
        <div class="sg-title">VOICE & INTERACTION</div>
        <div class="sg-row"><span class="sg-key">Wake Word</span><span class="sg-val">"JARVIS"</span></div>
        <div class="sg-row"><span class="sg-key">Launch</span><span class="sg-val">Double clap + phrase</span></div>
        <div class="sg-row"><span class="sg-key">Conv. Window</span><span class="sg-val">20 seconds</span></div>
        <div class="sg-row"><span class="sg-key">API config</span><span class="sg-val" style="color:var(--muted);font-size:9px">Managed by ULTRON</span></div>
      </div>
    </div>`;
}
</script>"""
