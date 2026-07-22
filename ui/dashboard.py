"""JARVIS Dashboard HTML — full UI redesign v2"""

# Part 1: head + CSS
_HEAD = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>JARVIS</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#010d18;--bg1:#031624;--bg2:#041e30;--panel:#051d2e;
  --border:#0a3a5a;--c1:#00d4ff;--c2:#00a8cc;--c3:#0077aa;
  --text:#c8e8f0;--muted:#3a6a80;--red:#ff3a3a;--green:#00ff88;
  --yellow:#ffd700;--orange:#ff8c00;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:'Courier New',monospace;overflow:hidden}
#app{display:flex;flex-direction:column;height:100vh}
#topbar{height:44px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid var(--border);background:var(--bg1);flex-shrink:0}
#main{display:flex;flex:1;overflow:hidden}
#bottombar{height:84px;display:flex;border-top:1px solid var(--border);background:var(--bg1);flex-shrink:0}
.tb-brand{font-size:22px;font-weight:700;letter-spacing:6px;color:var(--c1);text-shadow:0 0 20px rgba(0,212,255,.6)}
.tb-right{display:flex;align-items:center;gap:12px}
.tb-online{font-size:10px;letter-spacing:3px;color:var(--green);display:flex;align-items:center;gap:6px}
.tb-online::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:pulse-g 2s infinite}
@keyframes pulse-g{0%,100%{opacity:1}50%{opacity:.4}}
#sidebar-left{width:210px;border-right:1px solid var(--border);display:flex;flex-direction:column;background:var(--bg1);overflow:hidden;flex-shrink:0}
.sl-section{display:flex;flex-direction:column;overflow:hidden}
#crypto-section{border-bottom:1px solid var(--border);flex-shrink:0}
#news-section{flex:1;overflow:hidden}
.sl-header{padding:8px 12px;font-size:9px;letter-spacing:3px;color:var(--muted);border-bottom:1px solid var(--border);background:var(--bg2)}
.sl-body{overflow-y:auto;flex:1}
.sl-body::-webkit-scrollbar{width:3px}
.sl-body::-webkit-scrollbar-thumb{background:var(--border)}
.crypto-row{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid rgba(10,58,90,.4);cursor:default}
.crypto-row:hover{background:var(--bg2)}
.crypto-sym{font-size:10px;font-weight:700;color:var(--c1)}
.crypto-price{font-size:10px;color:var(--text)}
.crypto-chg{font-size:9px;font-weight:700}
.crypto-chg.up{color:var(--green)}.crypto-chg.dn{color:var(--red)}
.news-item{padding:8px 12px;border-bottom:1px solid rgba(10,58,90,.4);cursor:pointer}
.news-item:hover{background:var(--bg2)}
.news-title{font-size:9px;color:var(--text);line-height:1.4;margin-bottom:3px}
.news-src{font-size:8px;color:var(--muted)}
#center{flex:1;display:flex;flex-direction:column;align-items:center;position:relative;overflow:hidden;background:var(--bg)}
#viz-wrap{flex:1;width:100%;position:relative;display:flex;align-items:center;justify-content:center}
#viz-canvas{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none}
#core-wrap{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;gap:0}
#core-glow{position:absolute;width:220px;height:220px;border-radius:50%;background:radial-gradient(circle,rgba(0,212,255,.15) 0%,transparent 70%);pointer-events:none;animation:glow-pulse 3s ease-in-out infinite}
@keyframes glow-pulse{0%,100%{transform:scale(1);opacity:.6}50%{transform:scale(1.15);opacity:1}}
#core-svg{width:180px;height:180px;filter:drop-shadow(0 0 12px rgba(0,212,255,.5))}
.ring{transform-origin:center;animation:spin linear infinite}
.ring1{animation-duration:8s}.ring2{animation-duration:14s;animation-direction:reverse}.ring3{animation-duration:20s}
@keyframes spin{to{transform:rotate(360deg)}}
#chat-scroll{max-height:140px;width:100%;max-width:680px;overflow-y:auto;padding:0 20px;margin-top:12px}
#chat-scroll::-webkit-scrollbar{width:3px}
#chat-scroll::-webkit-scrollbar-thumb{background:var(--border)}
.msg{margin-bottom:8px;font-size:11px;line-height:1.5}
.msg.user{color:var(--c1)}.msg.user::before{content:'YOU ▸  ';color:var(--muted);font-size:9px}
.msg.assistant{color:var(--text)}.msg.assistant::before{content:'JARVIS ▸  ';color:var(--c1);font-size:9px}
.typing-dot{display:inline-block;animation:blink .8s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
#input-area{width:100%;max-width:680px;padding:12px 20px 16px;display:flex;gap:10px}
#cmd-input{flex:1;background:var(--bg2);border:1px solid var(--border);color:var(--text);padding:10px 16px;font-family:inherit;font-size:12px;letter-spacing:1px;outline:none;border-radius:2px}
#cmd-input:focus{border-color:var(--c1);box-shadow:0 0 0 1px rgba(0,212,255,.2)}
#cmd-input::placeholder{color:var(--muted)}
.send-btn{background:rgba(0,212,255,.1);border:1px solid var(--c1);color:var(--c1);padding:10px 20px;font-family:inherit;font-size:10px;letter-spacing:2px;cursor:pointer;border-radius:2px}
.send-btn:hover{background:rgba(0,212,255,.2)}
/* RIGHT SIDEBAR — settings pinned to bottom */
#sidebar-right{width:52px;border-left:1px solid var(--border);display:flex;flex-direction:column;align-items:center;padding:16px 0 12px;gap:12px;background:var(--bg1);flex-shrink:0}
#sidebar-right .sr-spacer{flex:1}
.icon-btn{width:36px;height:36px;border:1px solid var(--border);background:var(--bg2);border-radius:4px;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:16px;transition:all .2s;color:var(--muted)}
.icon-btn:hover{border-color:var(--c1);color:var(--c1);background:rgba(0,212,255,.08);box-shadow:0 0 10px rgba(0,212,255,.2)}
.icon-btn.active{border-color:var(--c1);color:var(--c1);background:rgba(0,212,255,.12)}
.bb-item{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;border-right:1px solid var(--border);gap:2px;transition:background .15s;padding:6px 8px;position:relative}
.bb-item:last-child{border-right:none}
.bb-item:hover{background:var(--bg2)}
.bb-item:active{background:rgba(0,212,255,.08)}
.bb-top-row{display:flex;align-items:center;gap:6px}
.bb-icon{font-size:16px}
.bb-label{font-size:7px;letter-spacing:2px;color:var(--muted);text-align:center}
.bb-val{font-size:12px;color:var(--c1);font-weight:700;text-align:center}
.bb-sub{font-size:9px;color:var(--text);text-align:center;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bb-detail-row{display:flex;gap:10px;align-items:center}
.bb-pill{font-size:8px;padding:1px 5px;border-radius:1px;border:1px solid var(--border);color:var(--muted)}
.bb-pill.urgent{border-color:var(--red);color:var(--red)}
.bb-pill.ok{border-color:var(--green);color:var(--green)}
.bb-pill.warn{border-color:var(--yellow);color:var(--yellow)}
/* MODAL */
#modal-overlay{display:none;position:fixed;inset:0;background:rgba(1,13,24,.85);z-index:100;align-items:center;justify-content:center;backdrop-filter:blur(4px)}
#modal-overlay.open{display:flex}
#modal-win{background:var(--bg1);border:1px solid var(--border);width:92vw;max-width:1300px;height:86vh;display:flex;flex-direction:column;border-radius:3px;box-shadow:0 0 60px rgba(0,212,255,.1)}
#modal-head{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border);flex-shrink:0}
#modal-title{font-size:13px;letter-spacing:4px;color:var(--c1)}
.modal-close{background:none;border:1px solid var(--border);color:var(--muted);width:28px;height:28px;cursor:pointer;font-size:14px;border-radius:2px}
.modal-close:hover{border-color:var(--c1);color:var(--c1)}
#modal-body{flex:1;overflow:auto;padding:20px}
#modal-body::-webkit-scrollbar{width:4px}
#modal-body::-webkit-scrollbar-thumb{background:var(--border)}
.m-cols{display:flex;gap:20px;height:100%}
.m-col{flex:1;display:flex;flex-direction:column;gap:12px;overflow:hidden}
.m-col-title{font-size:10px;letter-spacing:3px;color:var(--muted);padding-bottom:8px;border-bottom:1px solid var(--border);flex-shrink:0}
.m-scroll{flex:1;overflow-y:auto}
.m-scroll::-webkit-scrollbar{width:3px}
.m-scroll::-webkit-scrollbar-thumb{background:var(--border)}
/* TASKS */
.kanban{display:flex;gap:14px;height:100%}
.k-col{flex:1;display:flex;flex-direction:column;background:var(--bg2);border:1px solid var(--border);border-radius:3px;overflow:hidden;min-width:0}
.k-head{padding:10px 12px;font-size:9px;letter-spacing:2px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.k-body{flex:1;overflow-y:auto;padding:8px}
.k-body::-webkit-scrollbar{width:3px}
.k-body::-webkit-scrollbar-thumb{background:var(--border)}
.task-card{background:var(--bg1);border:1px solid var(--border);border-radius:2px;padding:9px 10px;margin-bottom:8px;border-left:3px solid var(--border);position:relative;cursor:grab}
.task-card.jarvis{border-left-color:var(--c1);box-shadow:inset 0 0 12px rgba(0,212,255,.05)}
.task-card.human{border-left-color:var(--yellow)}
.task-card.urgent{border-left-color:var(--red)}
.tc-title{font-size:10px;color:var(--text);margin-bottom:4px;padding-right:20px}
.tc-meta{display:flex;gap:6px;flex-wrap:wrap}
.tc-tag{font-size:8px;padding:2px 6px;border-radius:1px;background:var(--bg2);border:1px solid var(--border);color:var(--muted)}
.tc-tag.urgent{border-color:var(--red);color:var(--red)}
.tc-tag.high{border-color:var(--orange);color:var(--orange)}
.tc-tag.medium{border-color:var(--c3);color:var(--c2)}
.tc-tag.low{border-color:var(--muted);color:var(--muted)}
.tc-tag.jarvis{border-color:var(--c1);color:var(--c1)}
.tc-result{font-size:8px;color:var(--muted);margin-top:4px;font-style:italic}
.tc-delete{position:absolute;top:7px;right:8px;background:none;border:none;color:var(--muted);cursor:pointer;font-size:12px;line-height:1;padding:2px;border-radius:2px;transition:color .15s}
.tc-delete:hover{color:var(--red)}
.task-card.dragging{opacity:.4;cursor:grabbing}
.k-col.drag-over{border-color:var(--c1);background:rgba(0,212,255,.04)}
.k-delete-zone{display:none;position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(255,58,58,.15);border:2px dashed var(--red);border-radius:4px;padding:14px 40px;font-size:10px;letter-spacing:3px;color:var(--red);z-index:200;pointer-events:none;white-space:nowrap}
.k-delete-zone.visible{display:block}
.k-delete-zone.hot{background:rgba(255,58,58,.35);border-style:solid}
/* TASK SLIDER */
.task-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-shrink:0}
.task-slider{display:flex;background:var(--bg2);border:1px solid var(--border);border-radius:3px;overflow:hidden}
.ts-btn{background:none;border:none;color:var(--muted);padding:6px 14px;font-family:inherit;font-size:9px;letter-spacing:2px;cursor:pointer;transition:all .15s}
.ts-btn:hover{color:var(--text)}
.ts-btn.active{background:rgba(0,212,255,.15);color:var(--c1)}
/* TASK POPUP */
#task-popup-overlay{display:none;position:fixed;inset:0;background:rgba(1,13,24,.75);z-index:300;align-items:center;justify-content:center}
#task-popup-overlay.open{display:flex}
#task-popup{background:var(--bg1);border:1px solid var(--c1);padding:24px;width:420px;border-radius:3px;box-shadow:0 0 40px rgba(0,212,255,.15)}
.tp-title{font-size:12px;letter-spacing:3px;color:var(--c1);margin-bottom:20px}
.tp-field{width:100%;background:var(--bg2);border:1px solid var(--border);color:var(--text);padding:9px 12px;font-family:inherit;font-size:11px;outline:none;border-radius:2px;margin-bottom:10px}
.tp-field:focus{border-color:var(--c1)}
.tp-field::placeholder{color:var(--muted)}
.tp-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
.tp-date-row{display:flex;align-items:center;gap:10px;margin-bottom:16px}
.tp-date-label{font-size:9px;color:var(--muted);letter-spacing:2px;white-space:nowrap}
.tp-actions{display:flex;gap:8px;justify-content:flex-end}
/* WEATHER */
.weather-big{text-align:center;padding:20px 0}
.w-temp{font-size:72px;color:var(--c1);line-height:1;text-shadow:0 0 40px rgba(0,212,255,.4)}
.w-desc{font-size:14px;color:var(--text);letter-spacing:3px;margin:8px 0}
.w-city{font-size:10px;color:var(--muted);letter-spacing:4px}
.w-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:24px}
.w-card{background:var(--bg2);border:1px solid var(--border);padding:14px;border-radius:2px;text-align:center}
.w-card-label{font-size:8px;color:var(--muted);letter-spacing:2px;margin-bottom:6px}
.w-card-val{font-size:16px;color:var(--text)}
.forecast-row{display:flex;gap:10px;margin-top:20px;overflow-x:auto;padding-bottom:4px}
.fc-day{flex-shrink:0;background:var(--bg2);border:1px solid var(--border);padding:12px 16px;border-radius:2px;text-align:center;min-width:80px}
.fc-day-name{font-size:8px;color:var(--muted);letter-spacing:2px;margin-bottom:4px}
.fc-day-temp{font-size:14px;color:var(--c1)}
.fc-day-desc{font-size:8px;color:var(--muted);margin-top:4px}
/* CALENDAR */
.cal-layout{display:flex;gap:0;height:100%}
.cal-mini{width:220px;flex-shrink:0;border-right:1px solid var(--border);display:flex;flex-direction:column;padding:16px 12px}
.cal-mini-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cal-mini-title{font-size:11px;color:var(--c1);letter-spacing:2px}
.cal-nav-btn{background:none;border:1px solid var(--border);color:var(--muted);width:22px;height:22px;cursor:pointer;font-size:11px;border-radius:2px}
.cal-nav-btn:hover{border-color:var(--c1);color:var(--c1)}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}
.cal-dow{font-size:8px;color:var(--muted);text-align:center;padding:4px 0;letter-spacing:1px}
.cal-day{font-size:10px;text-align:center;padding:5px 2px;border-radius:2px;cursor:pointer;color:var(--muted);position:relative}
.cal-day:hover{background:var(--bg2);color:var(--text)}
.cal-day.today{color:var(--c1);font-weight:700}
.cal-day.selected{background:rgba(0,212,255,.2);color:var(--c1);border:1px solid var(--c1)}
.cal-day.has-events::after{content:'';position:absolute;bottom:2px;left:50%;transform:translateX(-50%);width:4px;height:4px;border-radius:50%;background:var(--c1)}
.cal-day-view{flex:1;display:flex;flex-direction:column;overflow:hidden}
.cal-day-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border);flex-shrink:0}
.cal-day-title{font-size:12px;color:var(--c1);letter-spacing:2px}
.cal-approve-btn{background:rgba(0,255,136,.1);border:1px solid var(--green);color:var(--green);padding:4px 12px;font-family:inherit;font-size:8px;letter-spacing:2px;cursor:pointer;border-radius:2px}
.cal-approve-btn:hover{background:rgba(0,255,136,.2)}
.cal-scroll{flex:1;overflow-y:auto;position:relative}
.cal-scroll::-webkit-scrollbar{width:4px}
.cal-scroll::-webkit-scrollbar-thumb{background:var(--border)}
.cal-hour-row{display:flex;border-bottom:1px solid rgba(10,58,90,.3);min-height:52px;position:relative}
.cal-hour-label{width:48px;flex-shrink:0;font-size:9px;color:var(--muted);padding:4px 8px 4px 0;text-align:right}
.cal-hour-slot{flex:1;position:relative;cursor:context-menu}
.cal-event-block{position:absolute;left:4px;right:4px;border-radius:2px;padding:3px 6px;font-size:9px;overflow:hidden;cursor:pointer;z-index:1}
.cal-event-block.normal{background:rgba(0,119,170,.35);border-left:3px solid var(--c1);color:var(--text)}
.cal-event-block.advised{background:rgba(0,212,255,.08);border:1px dashed rgba(0,212,255,.4);color:rgba(200,232,240,.6)}
.cal-event-block.advised:hover{border-style:solid;color:var(--text)}
/* CAL CONTEXT MENU */
#cal-ctx{display:none;position:fixed;z-index:400;background:var(--bg1);border:1px solid var(--border);border-radius:3px;min-width:160px;box-shadow:0 8px 32px rgba(0,0,0,.5)}
.cal-ctx-item{padding:9px 14px;font-size:10px;color:var(--text);cursor:pointer;letter-spacing:1px}
.cal-ctx-item:hover{background:var(--bg2);color:var(--c1)}
/* CAL NEW EVENT POPUP */
#cal-event-popup{display:none;position:fixed;z-index:410;background:var(--bg1);border:1px solid var(--c1);padding:20px;border-radius:3px;width:300px;box-shadow:0 0 30px rgba(0,212,255,.15)}
.cep-title{font-size:10px;letter-spacing:3px;color:var(--c1);margin-bottom:16px}
.cep-field{width:100%;background:var(--bg2);border:1px solid var(--border);color:var(--text);padding:8px 10px;font-family:inherit;font-size:10px;outline:none;border-radius:2px;margin-bottom:8px}
.cep-field:focus{border-color:var(--c1)}
.cep-field::placeholder{color:var(--muted)}
.cep-flag{display:flex;align-items:center;gap:8px;margin-bottom:10px;font-size:10px;color:var(--muted)}
.cep-flag input{accent-color:var(--c1)}
/* AGENT NETWORK */
.ant-wrap{display:flex;flex-direction:column;align-items:center;height:100%;position:relative;overflow:hidden}
#ant-canvas{position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0}
.ant-nodes{width:100%;height:100%;position:relative;z-index:1;pointer-events:none}
.ant-node{position:absolute;background:var(--bg2);border:1px solid var(--border);border-radius:3px;padding:12px 14px;pointer-events:all;cursor:pointer;transition:border-color .2s,box-shadow .2s}
.ant-node:hover{border-color:var(--c1);box-shadow:0 0 16px rgba(0,212,255,.2)}
.ant-node.jarvis-node{border-color:var(--c1);box-shadow:0 0 20px rgba(0,212,255,.15);cursor:default;min-width:220px}
.ant-node-name{font-size:12px;font-weight:700;letter-spacing:2px;margin-bottom:4px}
.ant-node-desc{font-size:9px;color:var(--muted);margin-bottom:10px;line-height:1.4}
.ant-task-list{display:flex;flex-direction:column;gap:4px;min-height:20px}
.ant-task-item{font-size:8px;padding:3px 6px;border-radius:1px;border-left:2px solid var(--border);color:var(--muted);background:var(--bg1)}
.ant-task-item.active{border-left-color:var(--c1);color:var(--c1)}
.ant-task-item.done{border-left-color:var(--green);color:var(--green)}
.ant-pulse-dot{width:8px;height:8px;border-radius:50%;position:absolute;pointer-events:none;z-index:2}
/* BRAIN */
.brain-tabs{display:flex;border-bottom:1px solid var(--border);margin-bottom:0;flex-shrink:0}
.brain-tab-btn{background:none;border:none;border-bottom:2px solid transparent;color:var(--muted);padding:10px 18px;font-family:inherit;font-size:9px;letter-spacing:2px;cursor:pointer;transition:all .15s}
.brain-tab-btn:hover{color:var(--text)}
.brain-tab-btn.active{color:var(--c1);border-bottom-color:var(--c1)}
.brain-content{flex:1;overflow:hidden;display:flex;flex-direction:column}
/* TODAY MEMORY */
.mem-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(10,58,90,.4);align-items:flex-start;position:relative}
.mem-time{font-size:8px;color:var(--muted);white-space:nowrap;padding-top:2px;min-width:48px}
.mem-text{font-size:10px;color:var(--text);line-height:1.5;flex:1}
.mem-hd-icon{font-size:12px;cursor:pointer;flex-shrink:0;opacity:.6;transition:opacity .15s}
.mem-hd-icon:hover{opacity:1}
/* HARD DRIVE */
.hd-layout{display:flex;height:100%;gap:0}
.hd-tabs{width:110px;flex-shrink:0;border-right:1px solid var(--border);display:flex;flex-direction:column;gap:0}
.hd-tab-btn{background:none;border:none;border-left:2px solid transparent;color:var(--muted);padding:12px 10px;font-family:inherit;font-size:9px;letter-spacing:1px;cursor:pointer;text-align:left;transition:all .15s}
.hd-tab-btn:hover{color:var(--text);background:var(--bg2)}
.hd-tab-btn.active{color:var(--c1);border-left-color:var(--c1);background:rgba(0,212,255,.06)}
.hd-canvas-wrap{flex:1;position:relative;overflow:hidden}
#hd-canvas{width:100%;height:100%;cursor:default}
#hd-tooltip{position:absolute;background:var(--bg2);border:1px solid var(--c1);padding:8px 12px;font-size:10px;pointer-events:none;display:none;color:var(--text);border-radius:2px;max-width:200px;z-index:10}
/* ROBOT DETAIL */
.robot-layout{display:flex;gap:16px;height:100%}
.robot-net-wrap{flex:1;position:relative;overflow:hidden}
#robot-canvas{width:100%;height:100%}
.robot-detail-panel{width:260px;flex-shrink:0;display:flex;flex-direction:column;gap:10px;overflow-y:auto}
.robot-detail-panel::-webkit-scrollbar{width:3px}
.robot-detail-panel::-webkit-scrollbar-thumb{background:var(--border)}
.rbot-card{background:var(--bg2);border:1px solid var(--border);border-radius:2px;padding:12px}
.rbot-card.active{border-color:var(--c1)}
.rbot-name{font-size:11px;color:var(--c1);margin-bottom:4px;letter-spacing:1px}
.rbot-desc{font-size:9px;color:var(--muted);margin-bottom:8px}
.rbot-progress{height:3px;background:var(--border);border-radius:1px;overflow:hidden;margin-bottom:6px}
.rbot-fill{height:100%;background:var(--c1);transition:width .5s;border-radius:1px}
.rbot-thought{font-size:12px;margin-bottom:4px}
.rbot-tools{font-size:8px;color:var(--muted)}
/* INBOX */
.email-item{background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--border);padding:12px 16px;margin-bottom:8px;border-radius:2px;cursor:pointer;display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.email-item:hover{border-color:var(--c3)}
.email-item.imp-high{border-left-color:var(--red)}
.email-item.imp-med{border-left-color:var(--yellow)}
.email-subject{font-size:11px;color:var(--text);margin-bottom:3px}
.email-from{font-size:9px;color:var(--muted)}
.email-badge{font-size:8px;padding:2px 6px;border-radius:1px;white-space:nowrap;flex-shrink:0}
.badge-high{background:rgba(255,58,58,.15);color:var(--red);border:1px solid rgba(255,58,58,.3)}
.badge-med{background:rgba(255,215,0,.1);color:var(--yellow);border:1px solid rgba(255,215,0,.3)}
.badge-low{background:rgba(58,106,128,.2);color:var(--muted);border:1px solid var(--border)}
/* SETTINGS */
.profile-hero{display:flex;align-items:center;gap:24px;padding:20px;background:var(--bg2);border:1px solid var(--border);border-radius:3px;margin-bottom:20px}
.profile-avatar{width:64px;height:64px;border-radius:50%;border:2px solid var(--c1);display:flex;align-items:center;justify-content:center;font-size:28px;background:rgba(0,212,255,.08);flex-shrink:0}
.profile-name{font-size:20px;color:var(--c1);letter-spacing:3px;margin-bottom:4px}
.profile-sub{font-size:10px;color:var(--muted);letter-spacing:2px}
.settings-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.setting-group{background:var(--bg2);border:1px solid var(--border);padding:16px;border-radius:2px}
.sg-title{font-size:9px;letter-spacing:3px;color:var(--muted);margin-bottom:12px}
.sg-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:10px}
.sg-key{color:var(--muted)}.sg-val{color:var(--text)}
.sg-val.on{color:var(--green)}.sg-val.off{color:var(--red)}
/* MISC */
.btn{background:rgba(0,212,255,.1);border:1px solid var(--c1);color:var(--c1);padding:8px 16px;font-family:inherit;font-size:9px;letter-spacing:2px;cursor:pointer;border-radius:2px}
.btn:hover{background:rgba(0,212,255,.2)}
.btn-ghost{background:none;border:1px solid var(--border);color:var(--muted);padding:8px 16px;font-family:inherit;font-size:9px;letter-spacing:2px;cursor:pointer;border-radius:2px}
.btn-ghost:hover{border-color:var(--c1);color:var(--c1)}
.empty{color:var(--muted);font-size:10px;padding:20px;text-align:center}
#speaking-text{min-height:24px;max-width:560px;width:100%;text-align:center;font-size:12px;color:var(--c1);letter-spacing:1px;padding:0 20px;transition:opacity .3s;opacity:0}
#speaking-text.active{opacity:1}
.spoken-word{opacity:.3;transition:opacity .15s;margin:0 2px;display:inline-block}
.spoken-word.said{opacity:1}
#brain-wrap{width:100%;height:100%;position:relative}
#brain-canvas{width:100%;height:100%;cursor:pointer}
#brain-tooltip{position:absolute;background:var(--bg2);border:1px solid var(--c1);padding:8px 12px;font-size:10px;pointer-events:none;display:none;color:var(--text);border-radius:2px;max-width:200px;z-index:10}
</style>
</head>"""

# Part 2: body HTML
_BODY = r"""<body>
<div id="app">
  <div id="topbar">
    <div class="tb-brand">JARVIS</div>
    <div class="tb-right"><div class="tb-online">ONLINE</div></div>
  </div>
  <div id="main">
    <!-- LEFT SIDEBAR -->
    <div id="sidebar-left">
      <div id="crypto-section" class="sl-section" style="max-height:200px;display:flex;flex-direction:column">
        <div class="sl-header">MARKETS</div>
        <div class="sl-body" id="crypto-list"><div class="empty">Loading...</div></div>
      </div>
      <div id="news-section" class="sl-section">
        <div class="sl-header">INTEL FEED</div>
        <div class="sl-body" id="news-list"><div class="empty">Loading...</div></div>
      </div>
    </div>
    <!-- CENTER -->
    <div id="center">
      <div id="viz-wrap">
        <canvas id="viz-canvas"></canvas>
        <div id="core-wrap">
          <div id="core-glow"></div>
          <div id="conv-badge" style="position:absolute;bottom:-28px;left:50%;transform:translateX(-50%);font-size:9px;letter-spacing:2px;color:#00d4ff;opacity:0;transition:opacity .4s;text-transform:uppercase;white-space:nowrap;text-shadow:0 0 8px #00d4ff;pointer-events:none;">◉ LISTENING</div>
          <svg id="core-svg" viewBox="0 0 180 180">
            <defs>
              <radialGradient id="cg" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="#00d4ff" stop-opacity=".9"/>
                <stop offset="60%" stop-color="#0077aa" stop-opacity=".4"/>
                <stop offset="100%" stop-color="#010d18" stop-opacity="0"/>
              </radialGradient>
              <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
            </defs>
            <circle cx="90" cy="90" r="80" fill="none" stroke="#0a3a5a" stroke-width="1"/>
            <g class="ring ring1" style="transform-origin:90px 90px">
              <circle cx="90" cy="90" r="72" fill="none" stroke="#00d4ff" stroke-width="1.2" stroke-dasharray="8 6" opacity=".6"/>
              <circle cx="90" cy="18" r="4" fill="#00d4ff" opacity=".8"/>
            </g>
            <g class="ring ring2" style="transform-origin:90px 90px">
              <circle cx="90" cy="90" r="58" fill="none" stroke="#00a8cc" stroke-width="1" stroke-dasharray="4 8" opacity=".5"/>
              <circle cx="90" cy="32" r="3" fill="#00a8cc" opacity=".7"/>
            </g>
            <g class="ring ring3" style="transform-origin:90px 90px">
              <circle cx="90" cy="90" r="44" fill="none" stroke="#0077aa" stroke-width=".8" stroke-dasharray="12 4" opacity=".4"/>
            </g>
            <polygon points="90,62 112,75 112,101 90,114 68,101 68,75" fill="none" stroke="#00d4ff" stroke-width="1.5" opacity=".7" filter="url(#glow)"/>
            <circle cx="90" cy="90" r="22" fill="url(#cg)" filter="url(#glow)"/>
            <circle cx="90" cy="90" r="10" fill="#00d4ff" opacity=".9" filter="url(#glow)"/>
            <circle cx="90" cy="90" r="4" fill="#ffffff" opacity=".95"/>
            <g stroke="#00d4ff" stroke-width=".6" opacity=".4">
              <line x1="90" y1="8" x2="90" y2="16"/><line x1="90" y1="164" x2="90" y2="172"/>
              <line x1="8" y1="90" x2="16" y2="90"/><line x1="164" y1="90" x2="172" y2="90"/>
            </g>
          </svg>
        </div>
      </div>
      <div id="speaking-text"></div>
      <div id="chat-scroll"></div>
      <div id="input-area">
        <button id="mute-btn" title="Mute microphone" onclick="toggleMute()"
          style="background:var(--bg2);border:1px solid var(--border);color:var(--muted);width:38px;height:38px;border-radius:2px;cursor:pointer;font-size:16px;flex-shrink:0;transition:all .2s">🎙</button>
        <input id="cmd-input" placeholder="SPEAK OR TYPE A COMMAND…" autocomplete="off" spellcheck="false"/>
        <button class="send-btn" onclick="sendMsg()">TRANSMIT</button>
      </div>
    </div>
    <!-- RIGHT ICON BAR — settings pinned to bottom -->
    <div id="sidebar-right">
      <div class="icon-btn" onclick="openModal('brain')" title="Memory & Brain">🧠</div>
      <div class="icon-btn" onclick="openModal('robot')" title="Agent Detail">🤖</div>
      <div style="width:36px;height:1px;background:var(--border);flex-shrink:0"></div>
      <div class="icon-btn agent-btn" onclick="launchAgent('ultron')" title="ULTRON — Security" style="border-color:#2a0a0a" onmouseover="this.style.borderColor='#cc0000';this.style.boxShadow='0 0 10px rgba(204,0,0,.3)'" onmouseout="this.style.borderColor='#2a0a0a';this.style.boxShadow=''">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#cc0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L3 7v5c0 5.5 3.8 10.7 9 12 5.2-1.3 9-6.5 9-12V7L12 2z"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="9" x2="12" y2="2"/></svg>
      </div>
      <div class="icon-btn agent-btn" onclick="launchAgent('vision')" title="VISION — Intelligence" style="border-color:#0a3020" onmouseover="this.style.borderColor='#00cc66';this.style.boxShadow='0 0 10px rgba(0,204,102,.3)'" onmouseout="this.style.borderColor='#0a3020';this.style.boxShadow=''">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00cc66" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      </div>
      <div class="icon-btn agent-btn" onclick="launchAgent('friday')" title="FRIDAY — Content" style="border-color:#1a2040" onmouseover="this.style.borderColor='#4488ff';this.style.boxShadow='0 0 10px rgba(68,136,255,.3)'" onmouseout="this.style.borderColor='#1a2040';this.style.boxShadow=''">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4488ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
      </div>
      <div class="icon-btn agent-btn" onclick="launchAgent('gresz')" title="GRESZ — Business" style="border-color:#1e2240" onmouseover="this.style.borderColor='#c8a840';this.style.boxShadow='0 0 10px rgba(200,168,64,.3)'" onmouseout="this.style.borderColor='#1e2240';this.style.boxShadow=''">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c8a840" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>
      </div>
      <!-- spacer pushes settings to bottom -->
      <div class="sr-spacer"></div>
      <div style="width:36px;height:1px;background:var(--border);flex-shrink:0"></div>
      <div class="icon-btn" onclick="openModal('settings')" title="Settings">⚙</div>
    </div>
  </div><!-- /main -->

  <!-- BOTTOM BAR -->
  <div id="bottombar">
    <div class="bb-item" onclick="openModal('weather')">
      <div class="bb-top-row"><div class="bb-icon">🌤</div><div class="bb-val" id="bb-w-temp">—</div></div>
      <div class="bb-sub" id="bb-w-cond">Loading…</div>
      <div class="bb-detail-row"><span class="bb-pill" id="bb-w-wind">— wind</span><span class="bb-pill" id="bb-w-humid">— humid</span></div>
      <div class="bb-label">WEATHER · PETERSFIELD</div>
    </div>
    <div class="bb-item" onclick="openModal('tasks')">
      <div class="bb-top-row"><div class="bb-icon">📋</div><div class="bb-val" id="bb-t-open">—</div></div>
      <div class="bb-sub" id="bb-t-sub">— open tasks</div>
      <div class="bb-detail-row">
        <span class="bb-pill urgent" id="bb-t-urgent" style="display:none">0 URGENT</span>
        <span class="bb-pill ok" id="bb-t-done">— done</span>
      </div>
      <div class="bb-label">TASKS</div>
    </div>
    <div class="bb-item" onclick="openModal('bots')">
      <div class="bb-top-row"><div class="bb-icon">🔬</div><div class="bb-val">5 AGENTS</div></div>
      <div class="bb-sub" id="bb-bot-status">JARVIS · Active</div>
      <div class="bb-detail-row"><span class="bb-pill ok">ONLINE</span><span class="bb-pill" id="bb-bot-tasks">— tasks run</span></div>
      <div class="bb-label">AGENT NETWORK</div>
    </div>
    <div class="bb-item" onclick="openModal('calendar')">
      <div class="bb-top-row"><div class="bb-icon">📅</div><div class="bb-val" id="bb-c-count">—</div></div>
      <div class="bb-sub" id="bb-c-next">No events</div>
      <div class="bb-detail-row"><span class="bb-pill" id="bb-c-time">—</span></div>
      <div class="bb-label">CALENDAR</div>
    </div>
    <div class="bb-item" onclick="openModal('inbox')">
      <div class="bb-top-row"><div class="bb-icon">✉</div><div class="bb-val" id="bb-i-count">—</div></div>
      <div class="bb-sub" id="bb-i-sub">No new mail</div>
      <div class="bb-detail-row"><span class="bb-pill warn" id="bb-i-imp" style="display:none">— HIGH PRIORITY</span></div>
      <div class="bb-label">INBOX</div>
    </div>
  </div>
</div><!-- /app -->

<!-- STANDBY OVERLAY -->
<div id="standby-overlay" onclick="standbyClick(event)"
  style="position:fixed;inset:0;background:rgba(1,13,24,.98);z-index:500;cursor:default;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;transition:opacity .8s">
  <div style="font-size:40px;letter-spacing:12px;color:#00d4ff;text-shadow:0 0 40px rgba(0,212,255,.5)">JARVIS</div>
  <div style="font-size:10px;letter-spacing:4px;color:#3a6a80">STANDBY MODE</div>
  <div id="standby-msg" style="font-size:11px;letter-spacing:3px;color:#3a6a80;margin-top:8px;text-align:center">DOUBLE CLAP + SAY "WAKE UP JARVIS"</div>
  <div id="standby-clap" style="font-size:9px;letter-spacing:3px;color:#00d4ff;opacity:0;transition:opacity .3s;margin-top:4px">◉ CLAP DETECTED — NOW SAY "WAKE UP JARVIS"</div>
  <div style="margin-top:24px;display:flex;gap:8px;opacity:.3">
    <div id="sb-dot1" style="width:8px;height:8px;border-radius:50%;background:#0a3a5a"></div>
    <div id="sb-dot2" style="width:8px;height:8px;border-radius:50%;background:#0a3a5a"></div>
    <div id="sb-dot3" style="width:8px;height:8px;border-radius:50%;background:#0a3a5a"></div>
  </div>
  <div id="sb-unlock-wrap" style="display:none;flex-direction:column;align-items:center;gap:8px;margin-top:8px" onclick="event.stopPropagation()">
    <div style="font-size:9px;letter-spacing:2px;color:#3a6a80">MANUAL OVERRIDE — ENTER PASSWORD</div>
    <div style="display:flex;gap:8px">
      <input id="sb-pw" type="password" placeholder="password…"
        style="background:transparent;border:1px solid #1a3a50;color:#00d4ff;padding:8px 14px;font-family:'Courier New',monospace;font-size:12px;letter-spacing:2px;outline:none;border-radius:2px;width:220px"
        onkeydown="if(event.key==='Enter') sbUnlock()" onfocus="event.stopPropagation()"/>
      <button onclick="sbUnlock()"
        style="background:transparent;border:1px solid #1a3a50;color:#00d4ff;padding:8px 16px;cursor:pointer;font-family:'Courier New',monospace;font-size:10px;letter-spacing:2px;border-radius:2px">UNLOCK</button>
    </div>
    <div id="sb-pw-err" style="font-size:9px;color:#cc4444;display:none;letter-spacing:1px">INCORRECT PASSWORD</div>
  </div>
  <div id="standby-mic-hint" style="position:absolute;bottom:24px;font-size:8px;letter-spacing:2px;color:#1a3a50">● MIC LISTENING</div>
  <div onclick="event.stopPropagation();sbShowUnlock()"
    style="position:absolute;bottom:20px;right:24px;font-size:8px;letter-spacing:1px;color:#0d2535;cursor:pointer;transition:color .2s;user-select:none"
    onmouseover="this.style.color='#1a4a6a'" onmouseout="this.style.color='#0d2535'">MANUAL</div>
</div>

<!-- DRAG-DELETE ZONE -->
<div class="k-delete-zone" id="k-delete-zone">⬛ DROP TO DELETE</div>

<!-- MODAL -->
<div id="modal-overlay" onclick="closeModal()">
  <div id="modal-win" onclick="event.stopPropagation()">
    <div id="modal-head">
      <div id="modal-title">WINDOW</div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div id="modal-body"></div>
  </div>
</div>

<!-- TASK CREATION POPUP -->
<div id="task-popup-overlay" onclick="if(event.target===this)closeTaskPopup()">
  <div id="task-popup" onclick="event.stopPropagation()">
    <div class="tp-title">+ NEW TASK</div>
    <input id="tp-title-input" class="tp-field" placeholder="Task title…" onkeydown="if(event.key==='Enter')submitTaskPopup()"/>
    <div class="tp-row">
      <select id="tp-pri" class="tp-field" style="margin-bottom:0">
        <option value="medium">MEDIUM PRIORITY</option>
        <option value="low">LOW PRIORITY</option>
        <option value="high">HIGH PRIORITY</option>
        <option value="urgent">URGENT</option>
      </select>
      <select id="tp-who" class="tp-field" style="margin-bottom:0">
        <option value="human">MY TASK</option>
        <option value="jarvis">JARVIS TASK</option>
      </select>
    </div>
    <div class="tp-date-row" style="margin-top:10px">
      <span class="tp-date-label">SCHEDULE DATE</span>
      <input type="date" id="tp-date" class="tp-field" style="flex:1;margin-bottom:0"/>
    </div>
    <div class="tp-actions">
      <button class="btn-ghost" onclick="closeTaskPopup()">CANCEL</button>
      <button class="btn" onclick="submitTaskPopup()">CREATE</button>
    </div>
  </div>
</div>

<!-- CALENDAR CONTEXT MENU -->
<div id="cal-ctx">
  <div class="cal-ctx-item" id="cal-ctx-new" onclick="calCtxNewEvent()">＋ New Event Here</div>
  <div class="cal-ctx-item" id="cal-ctx-accept" onclick="calCtxAccept()" style="display:none;color:var(--green)">✓ Accept JARVIS Suggestion</div>
</div>

<!-- CALENDAR NEW EVENT POPUP -->
<div id="cal-event-popup">
  <div class="cep-title">NEW EVENT</div>
  <input id="cep-name" class="cep-field" placeholder="Event name…"/>
  <input id="cep-location" class="cep-field" placeholder="Location (optional)…"/>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
    <input id="cep-time" type="time" class="cep-field" style="margin-bottom:0"/>
    <select id="cep-cat" class="cep-field" style="margin-bottom:0">
      <option value="work">WORK</option>
      <option value="meeting">MEETING</option>
      <option value="personal">PERSONAL</option>
      <option value="deadline">DEADLINE</option>
    </select>
  </div>
  <div class="cep-flag" style="margin-top:8px">
    <input type="checkbox" id="cep-flag"/>
    <label for="cep-flag">Flag for JARVIS to advise on</label>
  </div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:4px">
    <button class="btn-ghost" onclick="closeCepPopup()">CANCEL</button>
    <button class="btn" onclick="submitCepEvent()">ADD EVENT</button>
  </div>
</div>
</body>"""


# Assemble full HTML
from ui.dashboard_js import _SCRIPT

DASHBOARD_HTML = _HEAD + _BODY.replace('</body>', _SCRIPT + '\n</body>')
