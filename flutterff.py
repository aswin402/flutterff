#!/usr/bin/env python3
"""
flutterff - Flutter web dev launcher
Opens a native borderless mobile window using GTK + WebKit2 directly.
Includes a custom header bar for window dragging, resizing, and closing.

Requires:
    python3-gi gir1.2-webkit2-4.1 gir1.2-gtk-3.0

Usage:
    flutterff                  # 412x915 default mobile, hot reload on
    flutterff --size iphone    # iPhone 14 size
    flutterff --size 430x932   # custom size
    flutterff --profile        # less RAM, no debug overhead
    flutterff --offline        # force offline mode
    flutterff --list-sizes     # show all presets
    flutterff --port 3000      # custom port (auto-finds free port if taken)
"""

import subprocess
import sys
import re
import threading
import argparse
import signal
import socket
import os

# ── deps check ────────────────────────────────────────────────────────────────
try:
    import gi
    try:
        gi.require_version("WebKit2", "4.1")
    except ValueError:
        gi.require_version("WebKit2", "4.0")
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, WebKit2, GLib, Gio
except ImportError:
    print("\n[flutterff] python3-gi or WebKit2 not found.")
    print("Run:  sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1\n")
    sys.exit(1)

# ── ansi ──────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

VERSION = "1.4.0"

# ── device presets ────────────────────────────────────────────────────────────
DEVICE_PRESETS = {
    "mobile":       (412, 915),
    "mobile-small": (360, 800),
    "iphone":       (390, 844),
    "tablet":       (768, 1024),
    "desktop":      (1280, 800),
}

# ── globals ───────────────────────────────────────────────────────────────────
_flutter      = None
_window       = None
_webview      = None
_current_url  = None   # track last loaded URL for reload button
_flutter_lock = threading.Lock()

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_size(size_str):
    try:
        w, h = size_str.lower().split("x")
        return int(w), int(h)
    except Exception:
        print(f"{RED}Invalid size '{size_str}'. Use WxH e.g. 390x844{RESET}")
        sys.exit(1)

def check_online():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("pub.dev", 443))
        s.close()
        return True
    except Exception:
        return False

def find_free_port(start=8080, end=8200):
    for port in range(start, end):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
            s.close()
            return port
        except OSError:
            continue
    print(f"{RED}No free port found between {start}-{end}{RESET}")
    sys.exit(1)

def is_port_free(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", port))
        s.close()
        return True
    except OSError:
        return False

def load_url_in_gtk(url):
    global _current_url
    _current_url = url
    if _webview:
        _webview.load_uri(url)
    return False

def quit_gtk():
    Gtk.main_quit()
    return False

# ── flutter stdin helpers ─────────────────────────────────────────────────────
def send_flutter_key(key: str):
    """Send a keypress to Flutter's stdin (r = hot reload, R = hot restart)."""
    global _flutter
    with _flutter_lock:
        if _flutter and _flutter.poll() is None:
            try:
                _flutter.stdin.write(key.encode())
                _flutter.stdin.flush()
                print(f"{CYAN}► Sent '{key}' to Flutter{RESET}")
            except Exception as e:
                print(f"{RED}Failed to send key: {e}{RESET}")

def on_hot_reload(_btn):
    """Hot reload — press r then reload the webview."""
    send_flutter_key("r")
    # give flutter a moment to recompile then reload webview
    GLib.timeout_add(800, reload_webview)

def on_hot_restart(_btn):
    """Hot restart — press R then reload the webview."""
    send_flutter_key("R")
    GLib.timeout_add(1500, reload_webview)

def reload_webview():
    if _webview and _current_url:
        _webview.load_uri(_current_url)
    return False  # don't repeat

# ── flutter watcher ───────────────────────────────────────────────────────────
def run_flutter(cmd, port):
    global _flutter

    lib_pattern = re.compile(r'(http://(?:localhost|127\.0\.0\.1):\d+\S*)')
    url_loaded  = False

    try:
        _flutter = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,   # ← PIPE so we can send r/R
        )
    except FileNotFoundError:
        print(f"{RED}Flutter not found! Make sure 'flutter' is in your PATH.{RESET}")
        GLib.idle_add(quit_gtk)
        return

    for line in iter(_flutter.stdout.readline, b''):
        try:
            text = line.decode("utf-8", errors="replace").rstrip()
        except Exception:
            continue

        print(text)

        if not url_loaded:
            match = lib_pattern.search(text)
            found_url = None

            if match:
                found_url = match.group(1)
            elif port and ("serving" in text.lower() or "listening" in text.lower()):
                found_url = f"http://localhost:{port}"

            if found_url:
                url_loaded = True
                print(f"\n{GREEN}{BOLD}✔ Flutter ready — loading:{RESET} {CYAN}{found_url}{RESET}\n")
                GLib.idle_add(load_url_in_gtk, found_url)

    _flutter.wait()
    GLib.idle_add(quit_gtk)

# ── gtk window ────────────────────────────────────────────────────────────────
def build_window(width, height):
    global _window, _webview

    win = Gtk.Window()
    win.set_title("flutterff")
    win.set_default_size(width, height)
    win.set_resizable(True)

    # ── Header Bar ──
    hb = Gtk.HeaderBar()
    hb.set_show_close_button(True)
    hb.set_title("flutterff")
    hb.set_decoration_layout("menu:close")
    win.set_titlebar(hb)

    # ── Hot Reload button (r) ──
    reload_btn = Gtk.Button()
    reload_btn.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.MENU))
    reload_btn.set_tooltip_text("Hot Reload (r)")
    reload_btn.connect("clicked", on_hot_reload)
    hb.pack_end(reload_btn)

    # ── Hot Restart button (R) ──
    restart_btn = Gtk.Button()
    restart_btn.set_image(Gtk.Image.new_from_icon_name("system-reboot-symbolic", Gtk.IconSize.MENU))
    restart_btn.set_tooltip_text("Hot Restart (R)")
    restart_btn.connect("clicked", on_hot_restart)
    hb.pack_end(restart_btn)

    # ── Size Selector ──
    size_btn = Gtk.MenuButton()
    size_btn.set_image(Gtk.Image.new_from_icon_name("view-fullscreen-symbolic", Gtk.IconSize.MENU))
    size_btn.set_tooltip_text("Change Device Size")
    menu = Gtk.Menu()
    for name, (w, h) in DEVICE_PRESETS.items():
        item = Gtk.MenuItem(label=f"{name.replace('-', ' ').title()} ({w}x{h})")
        item.connect("activate", lambda i, w=w, h=h, n=name: on_size_change(w, h, n))
        menu.append(item)
    menu.show_all()
    size_btn.set_popup(menu)
    hb.pack_start(size_btn)

    # ── WebView ──
    context = WebKit2.WebContext.get_default()
    context.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    webview = WebKit2.WebView()
    webview.connect("context-menu", lambda *a: True)
    webview.load_uri("about:blank")
    vbox.pack_start(webview, True, True, 0)

    win.add(vbox)
    win.show_all()

    def on_destroy(_win):
        global _flutter
        print(f"\n{YELLOW}Stopping Flutter...{RESET}")
        with _flutter_lock:
            if _flutter and _flutter.poll() is None:
                _flutter.terminate()
                try:
                    _flutter.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    _flutter.kill()
                    _flutter.wait()
        print(f"{GREEN}Done.{RESET}")
        Gtk.main_quit()

    win.connect("destroy", on_destroy)

    _window  = win
    _webview = webview
    return win, webview

def on_size_change(width, height, name):
    if _window:
        print(f"{YELLOW}Resizing to {name} ({width}x{height}){RESET}")
        _window.resize(width, height)

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="flutterff",
        description="Flutter web dev in a native window with custom header bar.",
    )
    parser.add_argument("--port", "-p", type=int, default=8080)
    parser.add_argument("--no-hot", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--flavor", type=str, default=None)
    parser.add_argument("--size", "-s", type=str, default="mobile")
    parser.add_argument("--list-sizes", action="store_true")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--offline", action="store_true",
                        help="Skip pub.dev checks — use cached packages only")
    args = parser.parse_args()

    if args.version:
        print(f"flutterff v{VERSION}")
        sys.exit(0)

    if args.list_sizes:
        print(f"\n{BOLD}Available size presets:{RESET}")
        for name, (w, h) in DEVICE_PRESETS.items():
            tag = "  ← default" if name == "mobile" else ""
            print(f"  {CYAN}{name:<15}{RESET} {w}x{h}{tag}")
        print(f"\n  {CYAN}custom{RESET}          e.g. --size 430x932\n")
        sys.exit(0)

    if args.size in DEVICE_PRESETS:
        width, height = DEVICE_PRESETS[args.size]
    else:
        width, height = parse_size(args.size)

    # ── port resolution ────────────────────────────────────────────────────────
    port = args.port
    if not is_port_free(port):
        free = find_free_port(port + 1)
        print(f"{YELLOW}Port {port} is in use — using {free} instead{RESET}")
        port = free

    # ── offline detection ──────────────────────────────────────────────────────
    offline = args.offline
    if not offline:
        print(f"{YELLOW}Checking connectivity...{RESET}", end=" ", flush=True)
        if check_online():
            print(f"{GREEN}online{RESET}")
        else:
            print(f"{YELLOW}offline{RESET}")
            offline = True

    # ── build flutter command ──────────────────────────────────────────────────
    flutter_cmd = [
        "flutter", "run",
        "-d", "web-server",
        f"--web-port={port}",
    ]
    if args.profile:
        flutter_cmd.append("--profile")
    if args.no_hot:
        flutter_cmd.append("--no-hot")
    if args.flavor:
        flutter_cmd += ["--flavor", args.flavor]
    if offline:
        flutter_cmd.append("--no-pub")

    # ── startup info ───────────────────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}🦊 flutterff v{VERSION}{RESET}")
    print(f"{YELLOW}Size:{RESET}       {width}x{height}  ({args.size if args.size in DEVICE_PRESETS else 'custom'})")
    print(f"{YELLOW}Port:{RESET}       {port}")
    print(f"{YELLOW}Mode:{RESET}       {'profile' if args.profile else 'debug (web-server)'}")
    print(f"{YELLOW}Hot reload:{RESET} {'disabled' if args.no_hot else 'enabled — button or r in terminal'}")
    print(f"{YELLOW}Network:{RESET}    {'⚠ offline — skipping pub' if offline else '✔ online'}")
    print(f"\n{YELLOW}Starting Flutter...{RESET}\n")

    build_window(width, height)

    t = threading.Thread(target=run_flutter, args=(flutter_cmd, port), daemon=True)
    t.start()

    signal.signal(signal.SIGINT, lambda *a: GLib.idle_add(quit_gtk))

    Gtk.main()

if __name__ == "__main__":
    main()