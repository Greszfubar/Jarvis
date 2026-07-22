"""DesktopAgent — full macOS desktop control: mouse, keyboard, apps, screen."""
import asyncio
import logging
import subprocess
from pathlib import Path

from agents.base import BaseAgent
from core.memory import Memory

log = logging.getLogger("jarvis.desktop")
mem = Memory()


class DesktopAgent(BaseAgent):
    name = "desktop"

    def tools(self):
        return [
            self._tool("take_screenshot", "Take a screenshot and return a description of what's on screen.", {}),
            self._tool("open_app", "Open a macOS application.", {
                "app_name": {"type": "string", "description": "App name e.g. Safari, Spotify, Terminal"},
            }, required=["app_name"]),
            self._tool("close_app", "Quit a macOS application.", {
                "app_name": {"type": "string"},
            }, required=["app_name"]),
            self._tool("run_shell", "Execute a shell command and return output.", {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "description": "Timeout seconds (default 15)"},
            }, required=["command"]),
            self._tool("type_text", "Type text as keyboard input to the focused window.", {
                "text": {"type": "string"},
            }, required=["text"]),
            self._tool("press_key", "Press a keyboard shortcut e.g. 'cmd+c', 'return', 'escape'.", {
                "keys": {"type": "string", "description": "Key combo string"},
            }, required=["keys"]),
            self._tool("click", "Move mouse and click at screen coordinates.", {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"type": "string", "description": "left, right, double (default: left)"},
            }, required=["x", "y"]),
            self._tool("get_focused_app", "Get the name of the currently focused application.", {}),
            self._tool("set_volume", "Set system volume 0-100.", {
                "level": {"type": "integer"},
            }, required=["level"]),
            self._tool("notify", "Send a macOS system notification.", {
                "title":   {"type": "string"},
                "message": {"type": "string"},
                "sound":   {"type": "boolean"},
            }, required=["title", "message"]),
            self._tool("list_running_apps", "List all currently running applications.", {}),
            self._tool("clipboard_get", "Get current clipboard content.", {}),
            self._tool("clipboard_set", "Set clipboard content.", {
                "text": {"type": "string"},
            }, required=["text"]),
            self._tool("open_url", "Open a URL in the default browser.", {
                "url": {"type": "string"},
            }, required=["url"]),
        ]

    async def execute(self, method: str, params: dict):
        dispatch = {
            "take_screenshot":   self._screenshot,
            "open_app":          self._open_app,
            "close_app":         self._close_app,
            "run_shell":         self._run_shell,
            "type_text":         self._type_text,
            "press_key":         self._press_key,
            "click":             self._click,
            "get_focused_app":   self._focused_app,
            "set_volume":        self._set_volume,
            "notify":            self._notify,
            "list_running_apps": self._list_apps,
            "clipboard_get":     self._clipboard_get,
            "clipboard_set":     self._clipboard_set,
            "open_url":          self._open_url,
        }
        fn = dispatch.get(method)
        if not fn:
            return {"error": f"Unknown method: {method}"}
        return await asyncio.to_thread(fn, params)

    def _screenshot(self, _):
        import pyautogui
        from PIL import Image
        import io, base64
        path = "/tmp/jarvis_screen.png"
        pyautogui.screenshot(path)
        # Return base64 thumbnail for Claude vision (optional)
        img = Image.open(path)
        img.thumbnail((1280, 720))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        mem.log_event("desktop", "screenshot", {"path": path})
        return {"path": path, "size": img.size, "base64_thumbnail": b64}

    def _open_app(self, p):
        subprocess.Popen(["open", "-a", p["app_name"]])
        return {"status": "opened", "app": p["app_name"]}

    def _close_app(self, p):
        script = f'tell application "{p["app_name"]}" to quit'
        subprocess.run(["osascript", "-e", script], timeout=5)
        return {"status": "closed", "app": p["app_name"]}

    def _run_shell(self, p):
        timeout = p.get("timeout", 15)
        result = subprocess.run(
            p["command"], shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {"stdout": result.stdout[:2000], "stderr": result.stderr[:500], "returncode": result.returncode}

    def _type_text(self, p):
        import pyautogui
        pyautogui.typewrite(p["text"], interval=0.03)
        return {"status": "typed", "length": len(p["text"])}

    def _press_key(self, p):
        import pyautogui
        keys = p["keys"].lower().replace("cmd", "command").replace("ctrl", "ctrl")
        parts = [k.strip() for k in keys.split("+")]
        if len(parts) == 1:
            pyautogui.press(parts[0])
        else:
            pyautogui.hotkey(*parts)
        return {"status": "pressed", "keys": p["keys"]}

    def _click(self, p):
        import pyautogui
        button = p.get("button", "left")
        if button == "double":
            pyautogui.doubleClick(p["x"], p["y"])
        elif button == "right":
            pyautogui.rightClick(p["x"], p["y"])
        else:
            pyautogui.click(p["x"], p["y"])
        return {"status": "clicked", "x": p["x"], "y": p["y"]}

    def _focused_app(self, _):
        script = 'tell application "System Events" to return name of first process whose frontmost is true'
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        return {"app": r.stdout.strip()}

    def _set_volume(self, p):
        subprocess.run(["osascript", "-e", f"set volume output volume {p['level']}"], timeout=5)
        return {"status": "set", "volume": p["level"]}

    def _notify(self, p):
        sound = "with sound" if p.get("sound", False) else ""
        script = f'display notification "{p["message"]}" with title "{p["title"]}" {sound}'
        subprocess.run(["osascript", "-e", script], timeout=5)
        return {"status": "notified"}

    def _list_apps(self, _):
        script = 'tell application "System Events" to return name of every process whose background only is false'
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        apps = [a.strip() for a in r.stdout.strip().split(",")]
        return {"apps": apps}

    def _clipboard_get(self, _):
        r = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return {"content": r.stdout}

    def _clipboard_set(self, p):
        subprocess.run(["pbcopy"], input=p["text"], text=True)
        return {"status": "set"}

    def _open_url(self, p):
        subprocess.Popen(["open", p["url"]])
        return {"status": "opened", "url": p["url"]}
