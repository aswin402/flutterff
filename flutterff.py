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
    flutterff --list-sizes     # show all presets
    flutterff --port 3000      # custom port
"""

import subprocess
import sys
import re
import threading
import argparse
import signal

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

VERSION = "1.1.0"

# ── device presets ────────────────────────────────────────────────────────────
DEVICE_PRESETS = {
    "mobile":       (412, 915),
    "mobile-small": (360, 800),
    "iphone":       (390, 844),
    "tablet":       (768, 1024),
    "desktop":      (1280, 800),
}

# ── globals ───────────────────────────────────────────────────────────────────
_flutter = None
_window  = None
_webview = None

# ── helpers ───────────────────────────────────────────────────────────────────
def parse_size(size_str):
    try:
        w, h = size_str.lower().split("x")
        return int(w), int(h)
    except Exception:
        print(f"{RED}Invalid size '{size_str}'. Use WxH e.g. 390x844{RESET}")
        sys.exit(1)

def load_url_in_gtk(url):
    """Called from GLib main loop to safely navigate the webview."""
    if _webview:
        _webview.load_uri(url)
    return False

def quit_gtk():
    """Called from GLib main loop to safely quit GTK."""
    Gtk.main_quit()
    return False

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
            stdin=sys.stdin,
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
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    webview = WebKit2.WebView()
    webview.connect("context-menu", lambda *a: True)
    webview.load_uri("about:blank")
    vbox.pack_start(webview, True, True, 0)
    
    win.add(vbox)
    win.show_all()

    win.connect("destroy", Gtk.main_quit)

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

    flutter_cmd = [
        "flutter", "run",
        "-d", "web-server",
        f"--web-port={args.port}",
    ]
    if args.profile:
        flutter_cmd.append("--profile")
    if args.no_hot:
        flutter_cmd.append("--no-hot")
    if args.flavor:
        flutter_cmd += ["--flavor", args.flavor]

    print(f"\n{BOLD}{CYAN}🦊 flutterff v{VERSION}{RESET}")
    print(f"{YELLOW}Size:{RESET}       {width}x{height}  ({args.size if args.size in DEVICE_PRESETS else 'custom'})")
    print(f"\n{YELLOW}Starting Flutter...{RESET}\n")

    # build GTK window
    build_window(width, height)

    # start flutter watcher
    t = threading.Thread(target=run_flutter, args=(flutter_cmd, args.port), daemon=True)
    t.start()

    # handle ctrl+c
    signal.signal(signal.SIGINT, lambda *a: GLib.idle_add(quit_gtk))

    # GTK main loop
    Gtk.main()

    # cleanup
    print(f"\n{YELLOW}Stopping Flutter...{RESET}")
    if _flutter and _flutter.poll() is None:
        _flutter.terminate()
        _flutter.wait()
    print(f"{GREEN}Done.{RESET}")

if __name__ == "__main__":
    main()