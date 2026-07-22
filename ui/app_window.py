"""
JARVIS native app window — pywebview wrapper.

Lifecycle:
  1. webview.start(func=_boot) is called on the main thread.
  2. _boot() runs in a daemon thread:
       - starts uvicorn (FastAPI) on localhost:8765
       - waits until the server is accepting connections
       - loads the URL into the already-created (but blank) window
  3. Main thread keeps the WKWebView alive until the user closes it.
"""
import logging
import os
import socket
import threading
import time

import webview

log = logging.getLogger("jarvis.appwindow")

_HOST = "127.0.0.1"
_PORT = 8765

# JARVIS_OS=1 → MK II shell: fullscreen kiosk at /os instead of the MK I dashboard
_OS_MODE = os.environ.get("JARVIS_OS", "").lower() in ("1", "true", "yes")
_URL  = f"http://{_HOST}:{_PORT}" + ("/os" if _OS_MODE else "")

# The window handles — set in open_window(), used in _boot()
_win: webview.Window = None
_stage_win: webview.Window = None


def _wait_for_server(timeout: float = 15.0) -> bool:
    """Poll until the FastAPI server is accepting TCP connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((_HOST, _PORT), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def _boot(start_async_engine):
    """
    Called by webview in a background thread right after the window is created.
    Starts the FastAPI server and the async engine, then loads the URL.
    """
    # 1. Start the async engine (FastAPI + agents + scheduler + voice)
    #    This is a blocking call that runs forever — launch in its own thread.
    engine_thread = threading.Thread(
        target=start_async_engine, daemon=True, name="async-main"
    )
    engine_thread.start()

    # 2. Wait for the web server to be ready
    log.info("Waiting for JARVIS web server…")
    if _wait_for_server(timeout=20):
        log.info("Server ready — loading app window")
        if _win:
            _win.load_url(_URL)
        if _stage_win:
            _stage_win.load_url(f"http://{_HOST}:{_PORT}/stage")
    else:
        log.error("Server did not start in time — window will show error page")


def open_window(start_async_engine):
    """
    Create the native JARVIS window and start the app.
    Blocks until the user closes the window.
    Called from the main thread.
    """
    global _win
    from ui.sub_apps import JarvisAPI

    bg = "#000000" if _OS_MODE else "#010d18"
    _win = webview.create_window(
        title            = "JARVIS",
        url              = f"data:text/html,<html style='background:%23{bg[1:]}'></html>",
        width            = 1400,
        height           = 900,
        min_size         = (1100, 700),
        background_color = bg,
        text_select      = False,
        fullscreen       = _OS_MODE,      # MK II shell owns the whole screen
        js_api           = JarvisAPI(),   # exposes window.pywebview.api to JS
    )

    # OS mode + a second display → THE STAGE gets its own fullscreen window
    global _stage_win
    if _OS_MODE:
        try:
            screens = webview.screens
            if len(screens) > 1:
                _stage_win = webview.create_window(
                    title            = "THE STAGE",
                    url              = "data:text/html,<html style='background:%23000000'></html>",
                    background_color = "#000000",
                    text_select      = False,
                    fullscreen       = True,
                    screen           = screens[1],
                )
                log.info(f"STAGE window created on display 2 of {len(screens)}")
            else:
                log.info("One display detected — STAGE stays at /stage in a browser")
        except Exception as e:
            log.warning(f"STAGE window setup failed (continuing single-screen): {e}")

    # Pass start_async_engine as the func so webview calls it in a thread
    webview.start(
        func         = _boot,
        args         = (start_async_engine,),
        private_mode = False,        # allow localStorage / IndexedDB
        debug        = False,
    )
    # webview.start() returns when the window is closed
    log.info("JARVIS window closed — shutting down")
