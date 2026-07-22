// Event link — the existing MK I /ws endpoint carries chat + voice + OS events.
// Sending plain text = an utterance for the orchestrator.
// Incoming: {kind: clap_detected|launching|wake|got_command|speaking|speaking_done
//            |typing|response|alert|os|…}

export class EventLink {
  constructor(onEvent) {
    this.onEvent = onEvent;
    this._open();
  }

  _open() {
    this.ws = new WebSocket(`ws://${location.host}/ws`);
    this.ws.onmessage = (e) => {
      try { this.onEvent(JSON.parse(e.data)); } catch { /* ignore */ }
    };
    this.ws.onclose = () => setTimeout(() => this._open(), 2000);
    this.ws.onerror = () => this.ws.close();
  }

  say(text) {
    if (this.ws && this.ws.readyState === 1 && text.trim()) this.ws.send(text.trim());
  }
}
