// Mic capture → /ws/audio (16 kHz Int16 PCM, same pipeline as MK I dashboard).
// Also computes a local RMS level for the waveform — no server round-trip.

export class AudioLink {
  constructor({ onLevel } = {}) {
    this.onLevel = onLevel || (() => {});
    this.ws = null;
    this.ctxA = null;
    this.enabled = true;        // mic button state
    this.jarvisSpeaking = false; // gate: don't stream Jarvis's own voice
    this._speakTimer = null;
  }

  async start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      this.ctxA = new (window.AudioContext || window.webkitAudioContext)();
      if (this.ctxA.state === "suspended") await this.ctxA.resume();
      const source = this.ctxA.createMediaStreamSource(stream);
      const proc = this.ctxA.createScriptProcessor(4096, 1, 1);
      source.connect(proc);
      proc.connect(this.ctxA.destination);
      this._openWs();
      proc.onaudioprocess = (e) => {
        const f32 = e.inputBuffer.getChannelData(0);
        // Local level for the waveform (always, even when muted → shows silence)
        let sum = 0;
        for (let i = 0; i < f32.length; i += 4) sum += f32[i] * f32[i];
        this.onLevel(this.enabled ? Math.sqrt(sum / (f32.length / 4)) : 0);
        // Stream to server unless muted or Jarvis is talking
        if (!this.enabled || this.jarvisSpeaking) return;
        if (!this.ws || this.ws.readyState !== 1) return;
        this.ws.send(this._downsample(f32, this.ctxA.sampleRate).buffer);
      };
      return true;
    } catch (err) {
      console.warn("Audio capture failed:", err.message);
      return false;
    }
  }

  resume() { if (this.ctxA && this.ctxA.state === "suspended") this.ctxA.resume(); }

  setEnabled(on) {
    this.enabled = on;
    fetch("/api/mute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ muted: !on }),
    }).catch(() => {});
  }

  setSpeaking(on) {
    this.jarvisSpeaking = on;
    clearTimeout(this._speakTimer);
    // Failsafe: never stay gated longer than 30 s
    if (on) this._speakTimer = setTimeout(() => { this.jarvisSpeaking = false; }, 30000);
  }

  _openWs() {
    this.ws = new WebSocket(`ws://${location.host}/ws/audio`);
    this.ws.binaryType = "arraybuffer";
    this.ws.onclose = () => setTimeout(() => this._openWs(), 2000);
    this.ws.onerror = () => this.ws.close();
  }

  _downsample(f32, inputRate) {
    if (inputRate === 16000) {
      const out = new Int16Array(f32.length);
      for (let i = 0; i < f32.length; i++)
        out[i] = Math.max(-32768, Math.min(32767, f32[i] * 32768));
      return out;
    }
    const ratio = inputRate / 16000;
    const outLen = Math.floor(f32.length / ratio);
    const out = new Int16Array(outLen);
    for (let i = 0; i < outLen; i++) {
      const src = f32[Math.floor(i * ratio)];
      out[i] = Math.max(-32768, Math.min(32767, src * 32768));
    }
    return out;
  }
}
