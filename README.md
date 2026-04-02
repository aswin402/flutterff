# FlutterFF (logo etc full content as above)
  <img src="asset/logo.png" width="180" alt="flutterff logo" />
  <h1>flutterff</h1>
  <p><b>Lightweight native Flutter web development launcher for Linux</b></p>
  <code>v1.5.0</code>
</div>

---

**flutterff** is a minimal, borderless web development launcher designed specifically for Flutter developers. It uses **GTK 3** and **WebKit2** directly, bypassing the heavy overhead of Chromium-based browsers, while providing a modern mobile-first preview experience.

## ✨ Features (v1.1.0)
- 🦊 **Native Header Bar**: Custom draggable bar for window management.
- ❌ **Native Close Button**: Standard window controls for a desktop feel.
- 📱 **Integrated Size Selector**: Change device sizes (Mobile, iPhone, Tablet) instantly via a dropdown menu.
- 🚀 **Performance**: Extremely low RAM usage compared to a full browser.
- 🛠️ **Flutter Focused**: Auto-loads your Flutter web server, supports Hot Reload, and handles common development ports.
- 🗔 **Draggable & Resizable**: Move the window anywhere; change sizes on the fly.

## 🛠️ Prerequisites
Before running `flutterff`, ensure you have the necessary GTK and WebKit libraries installed:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

## 🚀 Installation & Update
Run the following script in the project directory to install or update your global `flutterff` command:

```bash
bash update.sh
```

## 📖 Usage
```bash
flutterff                  # 412x915 default mobile (Pixel 7 Pro)
flutterff --size iphone    # iPhone 14 size
flutterff --size 360x800   # Custom mobile size
flutterff --list-sizes     # See all presets
flutterff --port 3000      # Use a custom development port
flutterff --profile        # Run in Flutter profile mode
```

## ⌨️ Shortcuts & Controls
- **Drag**: Click and drag the header bar at the top.
- **Resize**: Click the "Maximize" icon in the header bar to pick a new size.
- **Exit**: Click the Close (X) button or press `Ctrl + C` in your terminal.
- **Hot Reload**: Press `r` in the terminal while `flutterff` is running.

---
<p align="center">Made for Flutter developers who value performance and desktop integration.</p>
