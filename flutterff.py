#!/usr/bin/env python3
"""
flutterff - Flutter web dev launcher
Opens a native borderless mobile window using GTK + WebKit2 directly.

Requires:
    python3-gi gir1.2-webkit2-4.1 gir1.2-gtk-3.0

Usage:
    flutterff                  # 412x915 default mobile, hot reload on
    flutterff --size iphone    # iPhone 14 size
    flutterff --size 430x932   # custom size
    flutterff --profile        # less RAM, no debug overhead
    flutterff --offline        # force offline mode
    flutterff --list-sizes     # show all presets
    flutterff --port 3000      # custom port
"""

import subprocess
import sys
import re
import threading
import argparse
import signal
import socket
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import time

try:
    import gi
    try:
        gi.require_version("WebKit2", "4.1")
    except ValueError:
        gi.require_version("WebKit2", "4.0")
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, WebKit2, GLib, Gdk, GdkPixbuf
except ImportError:
    print("\n[flutterff] python3-gi or WebKit2 not found.")
    print("Run:  sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1\n")
    sys.exit(1)

# ── ansi ──────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

VERSION = "2.4.0"

DEVICE_PRESETS: Dict[str, Tuple[int, int]] = {
    "mobile":       (412, 915),
    "mobile-small": (360, 800),
    "iphone":       (390, 844),
    "tablet":       (768, 1024),
    "desktop":      (1280, 800),
}

_flutter:      Optional[subprocess.Popen] = None
_window:       Optional[Gtk.Window]       = None
_webview:      Optional[WebKit2.WebView]  = None
_current_url:  Optional[str]              = None
_flutter_lock  = threading.Lock()
_pending_url:  Optional[str]              = None
_pending_lock  = threading.Lock()
_project_root: str                        = os.getcwd()

_ANSI = re.compile(r'\x1b\[[0-9;]*m')

def _strip(t: str) -> str:
    return _ANSI.sub('', t).strip()

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")

def any_in(text: str, patterns: list) -> bool:
    lo = text.lower()
    return any(p in lo for p in patterns)

# ── log levels ────────────────────────────────────────────────────────────────
def _detect_level(text: str) -> Tuple[str, str]:
    lo = text.lower()
    if any_in(lo, ["error:", "exception:", "fatal:", "unhandled"]):
        return "ERR", RED
    elif any_in(lo, ["warning:", "warn:", "deprecated"]):
        return "WRN", YELLOW
    elif "debug:" in lo:
        return "DBG", DIM
    else:
        return "INF", BLUE

def format_flutter_log(raw: str, source: str = "flutter") -> Optional[str]:
    lo_raw = raw.lower()
    if any_in(lo_raw, [
        "http://", "https://", ".js:", "console",
        "flutter_bootstrap", "ddc_module_loader",
        "dart_sdk", "web_entrypoint"
    ]):
        return None

    text = _strip(raw)
    if not text:
        return None

    lo = text.lower()
    ts = _ts()

    if "flutter:" in lo:
        parts = re.split(r'flutter:\s*', text, flags=re.IGNORECASE)
        msg = parts[-1].strip() if len(parts) > 1 else text
        if not msg:
            return None
        tag, color = _detect_level(msg)
        return f"{ts}  {color}{tag}{RESET}  {msg}"

    if source == "webview":
        tag, color = _detect_level(text)
        return f"{ts}  {color}{tag}{RESET}  {text}"

    if any_in(lo, ["error:", "exception:", "fatal:", "══╡", "══╞"]):
        return f"{ts}  {RED}ERR{RESET}  {text}"

    return None

# ── screenshot ────────────────────────────────────────────────────────────────
def take_screenshot():
    """Capture the webview using GTK/Cairo.
    This guarantees we read exactly what is rendered, bypassing WebKit internal
    snapshot bugs on resize and Wayland window grab issues.
    """
    if not _webview:
        print(f"{_ts()}  {RED}ERR{RESET}  no webview available")
        return

    shots_dir = os.path.join(_project_root, "screenshots")
    os.makedirs(shots_dir, exist_ok=True)

    fname = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
    fpath = os.path.join(shots_dir, fname)

    def _do_capture():
        try:
            import cairo
        except ImportError:
            print(f"{_ts()}  {RED}ERR{RESET}  python3-cairo required for screenshots")
            return False

        try:
            alloc = _webview.get_allocation()
            w, h = alloc.width, alloc.height
            if w <= 0 or h <= 0:
                print(f"{_ts()}  {RED}ERR{RESET}  invalid webview size")
                return False

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            cr = cairo.Context(surface)
            _webview.draw(cr)
            
            surface.write_to_png(fpath)
            print(f"{_ts()}  {GREEN}SCR{RESET}  saved → screenshots/{fname}  ({w}x{h})")
        except Exception as e:
            print(f"{_ts()}  {RED}ERR{RESET}  screenshot failed: {e}")

        return False

    def _queue_capture():
        # Flush pending GTK redraws first, then capture
        _webview.queue_draw()
        GLib.timeout_add(300, _do_capture)
        return False

    GLib.idle_add(_queue_capture)

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_size(size_str: str) -> Tuple[int, int]:
    try:
        w, h = size_str.lower().split("x")
        return int(w), int(h)
    except Exception:
        print(f"{RED}invalid size '{size_str}' — use WxH e.g. 390x844{RESET}")
        sys.exit(1)

def check_online() -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 53))
        s.close()
        return True
    except Exception:
        return False

def find_free_port(start: int = 8080, end: int = 8200) -> int:
    for p in range(start, end):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", p))
            s.close()
            return p
        except OSError:
            continue
    print(f"{RED}no free port found between {start}-{end}{RESET}")
    sys.exit(1)

def is_port_free(port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        s.close()
        return True
    except OSError:
        return False

def load_url_in_gtk(url: str) -> bool:
    global _current_url
    _current_url = url
    if _webview:
        def attempt_load(remaining: int):
            try:
                port = int(url.split(":")[2].split("/")[0])
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                s.close()
                if _webview:
                    _webview.load_uri(url)
                    print(f"{_ts()}  {GREEN}SRV{RESET}  serving on :{port}")
                return False
            except Exception:
                if remaining > 0:
                    GLib.timeout_add(500, lambda: attempt_load(remaining - 1))
                return False
        attempt_load(15)
    return False

def quit_gtk() -> bool:
    Gtk.main_quit()
    return False

# ── flutter stdin ─────────────────────────────────────────────────────────────
def send_flutter_key(key: str):
    global _flutter
    with _flutter_lock:
        if _flutter and _flutter.poll() is None:
            try:
                _flutter.stdin.write(key.encode())
                _flutter.stdin.flush()
                label = "hot reload" if key == "r" else "hot restart"
                print(f"{_ts()}  {CYAN}HOT{RESET}  {label}")
            except Exception as e:
                print(f"{_ts()}  {RED}ERR{RESET}  key send failed: {e}")

def reload_webview() -> bool:
    if _webview and _current_url:
        def attempt_reload(remaining: int):
            try:
                if _webview:
                    _webview.load_uri(_current_url)
                return False
            except Exception:
                if remaining > 0:
                    GLib.timeout_add(500, lambda: attempt_reload(remaining - 1))
                return False
        attempt_reload(10)
    return False

# ── flutter watcher ───────────────────────────────────────────────────────────
def run_flutter(cmd: list, port: int):
    global _flutter

    lib_pattern = re.compile(r'(http://(?:localhost|127\.0\.0\.1):\d+\S*)')
    url_sent = False

    try:
        _flutter = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )
    except FileNotFoundError:
        print(f"{_ts()}  {RED}ERR{RESET}  flutter not found — check PATH")
        GLib.idle_add(quit_gtk)
        return

    def _read_stderr(proc):
        for line in proc.stderr:
            out = format_flutter_log(line)
            if out:
                print(out, flush=True)

    threading.Thread(target=_read_stderr, args=(_flutter,), daemon=True).start()

    for line in _flutter.stdout:
        if not url_sent:
            match = lib_pattern.search(line)
            found_url = match.group(1) if match else None
            if not found_url and port:
                lo = line.lower()
                if "serving" in lo or "listening" in lo:
                    found_url = f"http://localhost:{port}"
            if found_url:
                url_sent = True
                GLib.idle_add(load_url_in_gtk, found_url)

        out = format_flutter_log(line)
        if out:
            print(out)

    _flutter.wait()
    GLib.idle_add(quit_gtk)

# ── gtk window ────────────────────────────────────────────────────────────────
def build_window(width: int, height: int):
    global _window, _webview

    win = Gtk.Window()
    win.set_title("flutterff")
    win.set_default_size(width, height)
    win.set_resizable(True)

    hb = Gtk.HeaderBar()
    hb.set_show_close_button(True)
    hb.set_title("flutterff")
    hb.set_decoration_layout("menu:close")
    win.set_titlebar(hb)

    # ── size selector ──────────────────────────────────────────────────────────
    size_btn = Gtk.MenuButton()
    size_btn.set_image(
        Gtk.Image.new_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.MENU))
    size_btn.set_tooltip_text("Change Device Size")
    menu = Gtk.Menu()
    for name, (w, h) in DEVICE_PRESETS.items():
        label = f"{name.replace('-', ' ').title()} ({w}x{h})"
        item = Gtk.MenuItem(label=label)
        item.connect("activate", lambda i, w=w, h=h, n=name: on_size_change(w, h, n))
        menu.append(item)
    menu.show_all()
    size_btn.set_popup(menu)
    hb.pack_start(size_btn)

    # ── screenshot button ──────────────────────────────────────────────────────
    shot_btn = Gtk.Button()
    shot_btn.set_image(
        Gtk.Image.new_from_icon_name("camera-photo-symbolic", Gtk.IconSize.MENU))
    shot_btn.set_tooltip_text("Screenshot (screenshots/)")
    shot_btn.connect("clicked", lambda _: take_screenshot())
    hb.pack_start(shot_btn)

    # ── hot reload ⚡ ──────────────────────────────────────────────────────────
    reload_btn = Gtk.Button()
    reload_lbl = Gtk.Label()
    reload_lbl.set_markup("<span>🗲</span>")
    reload_btn.add(reload_lbl)
    reload_btn.set_tooltip_text("Hot Reload (r)")
    reload_btn.connect("clicked", lambda btn: on_hot_reload(btn))
    hb.pack_end(reload_btn)

    # ── hot restart ────────────────────────────────────────────────────────────
    restart_btn = Gtk.Button()
    restart_btn.set_image(
        Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.MENU))
    restart_btn.set_tooltip_text("Hot Restart (R)")
    restart_btn.connect("clicked", lambda btn: on_hot_restart(btn))
    hb.pack_end(restart_btn)

    # ── webview ────────────────────────────────────────────────────────────────
    context = WebKit2.WebContext.get_default()
    context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)
    settings = WebKit2.Settings()
    settings.set_enable_write_console_messages_to_stdout(False)
    settings.set_enable_developer_extras(True)

    manager = WebKit2.UserContentManager()
    manager.register_script_message_handler("flutterLog")

    def on_script_message(_manager, js_result):
        try:
            msg = js_result.get_js_value().to_string()
            if msg:
                out = format_flutter_log(msg, source="webview")
                if out:
                    print(out, flush=True)
        except Exception:
            pass

    manager.connect("script-message-received::flutterLog", on_script_message)
    manager.add_script(WebKit2.UserScript(
        """(function(){
            ['log','warn','error','info','debug'].forEach(function(l){
                var o=console[l];
                console[l]=function(){
                    var m=Array.prototype.slice.call(arguments).join(' ');
                    try{window.webkit.messageHandlers.flutterLog.postMessage(m);}catch(e){}
                    o.apply(console,arguments);
                };
            });
        })();""",
        WebKit2.UserContentInjectedFrames.ALL_FRAMES,
        WebKit2.UserScriptInjectionTime.START,
        None, None
    ))

    webview = WebKit2.WebView.new_with_user_content_manager(manager)
    webview.set_settings(settings)
    webview.connect("context-menu", lambda *a: True)
    webview.load_uri("about:blank")

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    vbox.pack_start(webview, True, True, 0)
    win.add(vbox)
    win.show_all()

    def on_destroy(_win):
        global _flutter
        print(f"{_ts()}  {YELLOW}BYE{RESET}  stopping flutter...")
        with _flutter_lock:
            if _flutter and _flutter.poll() is None:
                _flutter.terminate()
                try:
                    _flutter.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    _flutter.kill()
                    _flutter.wait()
        print(f"{_ts()}  {GREEN}BYE{RESET}  done")
        Gtk.main_quit()

    win.connect("destroy", on_destroy)
    _window  = win
    _webview = webview
    return win, webview

def on_hot_reload(_btn):
    send_flutter_key("r")
    GLib.timeout_add(800, reload_webview)

def on_hot_restart(_btn):
    send_flutter_key("R")
    GLib.timeout_add(1500, reload_webview)

def on_size_change(width: int, height: int, name: str):
    if _window:
        print(f"{_ts()}  {CYAN}WIN{RESET}  {name} ({width}x{height})")
        _window.resize(width, height)
        
        # Force webview to update its layout
        if _webview:
            # Queue a resize event
            _webview.queue_resize()
            # Force a redraw after the resize
            def force_redraw():
                _webview.queue_draw()
                return False
            GLib.timeout_add(100, force_redraw)

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    global _project_root
    _project_root = os.getcwd()

    parser = argparse.ArgumentParser(prog="flutterff")
    parser.add_argument("--port",       "-p", type=int, default=8080)
    parser.add_argument("--no-hot",     action="store_true")
    parser.add_argument("--profile",    action="store_true")
    parser.add_argument("--flavor",     type=str, default=None)
    parser.add_argument("--size",       "-s", type=str, default="mobile")
    parser.add_argument("--list-sizes", action="store_true")
    parser.add_argument("--version",    action="store_true")
    parser.add_argument("--offline",    action="store_true")
    args = parser.parse_args()

    if args.version:
        print(f"🦊flutterff v{VERSION}"); sys.exit(0)

    if args.list_sizes:
        print(f"\n{BOLD}size presets{RESET}")
        print(f"{DIM}{'─'*30}{RESET}")
        for name, (w, h) in DEVICE_PRESETS.items():
            tag = f"  {DIM}default{RESET}" if name == "mobile" else ""
            print(f"  {CYAN}{name:<15}{RESET} {w}x{h}{tag}")
        print(f"  {CYAN}{'custom':<15}{RESET} e.g. --size 430x932\n")
        sys.exit(0)

    if args.size in DEVICE_PRESETS:
        width, height = DEVICE_PRESETS[args.size]
        size_label = args.size
    else:
        width, height = parse_size(args.size)
        size_label = "custom"

    port = args.port
    if not is_port_free(port):
        free_port = find_free_port(port + 1)
        print(f"{YELLOW}WRN{RESET}  port {port} in use \u2192 {free_port}")
        port = free_port

    offline = args.offline
    if not offline:
        print(f"{DIM}checking connectivity...{RESET} ", end="", flush=True)
        if check_online():
            print(f"{GREEN}online{RESET}")
        else:
            print(f"{YELLOW}offline{RESET}")
            offline = True

    flutter_cmd = ["flutter", "run", "-d", "web-server", f"--web-port={port}"]
    if args.profile: flutter_cmd.append("--profile")
    if args.no_hot:  flutter_cmd.append("--no-hot")
    if args.flavor:  flutter_cmd += ["--flavor", args.flavor]
    if offline:      flutter_cmd += ["--no-pub", "--no-web-resources-cdn"]

    print(f"\n{BOLD}flutterff{RESET} {DIM}v{VERSION}{RESET}")
    print(f"{DIM}{'─'*30}{RESET}")
    print(f"  {DIM}size{RESET}   {width}\u00d7{height}  {DIM}{size_label}{RESET}")
    print(f"  {DIM}port{RESET}   {port}")
    print(f"  {DIM}mode{RESET}   {'profile' if args.profile else 'debug'}")
    print(f"  {DIM}net{RESET}    {'offline' if offline else 'online'}")
    print(f"  {DIM}shots{RESET}  {_project_root}/screenshots/")
    print(f"{DIM}{'─'*30}{RESET}")
    print(f"\n{DIM}  time      tag  message{RESET}")
    print(f"{DIM}{'─'*30}{RESET}\n")

    build_window(width, height)
    threading.Thread(target=run_flutter, args=(flutter_cmd, port), daemon=True).start()
    signal.signal(signal.SIGINT, lambda *a: GLib.idle_add(quit_gtk))
    Gtk.main()

if __name__ == "__main__":
    main()