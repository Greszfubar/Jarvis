#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   J.A.R.V.I.S  —  Setup                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

JARVIS_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install via: brew install python@3.12"
  exit 1
fi

PYTHON=$(which python3)
echo "Using Python: $PYTHON ($($PYTHON --version))"

# ── Homebrew deps ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Checking system dependencies..."
for pkg in portaudio ffmpeg; do
  if ! brew list $pkg &>/dev/null; then
    echo "  Installing $pkg via Homebrew..."
    brew install $pkg
  else
    echo "  $pkg ✓"
  fi
done

# ── Virtual environment ───────────────────────────────────────────────────────
echo ""
echo "▶ Creating virtual environment..."
if [ ! -d "$JARVIS_DIR/.venv" ]; then
  $PYTHON -m venv "$JARVIS_DIR/.venv"
fi
source "$JARVIS_DIR/.venv/bin/activate"

echo "▶ Installing Python packages..."
pip install --quiet --upgrade pip
pip install --quiet -r "$JARVIS_DIR/requirements.txt"

# ── Config ────────────────────────────────────────────────────────────────────
echo ""
echo "▶ Setting up configuration..."
if [ ! -f "$JARVIS_DIR/config/.env" ]; then
  cp "$JARVIS_DIR/config/.env.example" "$JARVIS_DIR/config/.env"
  echo ""
  echo "  ┌─────────────────────────────────────────────────────┐"
  echo "  │  config/.env has been created.                      │"
  echo "  │  REQUIRED: add your ANTHROPIC_API_KEY               │"
  echo "  │  OPTIONAL: add NEWS_API_KEY, OPENWEATHER_API_KEY,   │"
  echo "  │            GOOGLE_CREDENTIALS_PATH                  │"
  echo "  └─────────────────────────────────────────────────────┘"
  echo ""
  echo "  Edit it now? (y/n)"
  read -r ans
  if [ "$ans" = "y" ]; then
    "${EDITOR:-nano}" "$JARVIS_DIR/config/.env"
  fi
fi

# ── macOS permissions reminder ────────────────────────────────────────────────
echo ""
echo "▶ macOS permissions required:"
echo "  → System Preferences → Privacy & Security"
echo "  → Microphone       : allow Terminal / your Python"
echo "  → Accessibility    : allow Terminal (for desktop control)"
echo "  → Screen Recording : allow Terminal (for screenshots)"
echo "  → Automation       : allow Terminal → Calendar, Reminders, System Events"
echo ""
echo "  Press Enter when permissions are set..."
read -r

# ── launchd plist for always-on ───────────────────────────────────────────────
PLIST_PATH="$HOME/Library/LaunchAgents/io.jarvis.assistant.plist"
echo "▶ Installing launchd daemon (always-on on login)..."
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>io.jarvis.assistant</string>
  <key>ProgramArguments</key>
  <array>
    <string>$JARVIS_DIR/.venv/bin/python</string>
    <string>$JARVIS_DIR/main.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$JARVIS_DIR</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$JARVIS_DIR/logs/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$JARVIS_DIR/logs/stderr.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
  </dict>
</dict>
</plist>
PLIST

launchctl load "$PLIST_PATH" 2>/dev/null || true
echo "  launchd plist installed at: $PLIST_PATH"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Setup complete!                        ║"
echo "║                                          ║"
echo "║   Run JARVIS now:                        ║"
echo "║     source .venv/bin/activate            ║"
echo "║     python main.py                       ║"
echo "║                                          ║"
echo "║   Dashboard: http://localhost:8765       ║"
echo "║   Wake: clap + 'Wake up JARVIS'          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
