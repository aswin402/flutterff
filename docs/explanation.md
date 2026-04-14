# What is flutterff?

**flutterff** (Flutter Fast Forward) is a specialized development launcher that bridges the gap between the heavy overhead of modern web browsers and the need for a native-feeling mobile preview during Flutter web development.

## The Problem

Flutter web development typically requires opening a browser like Chrome or Firefox. While powerful, these browsers bring significant overhead:
- **RAM Usage**: Chromium-based browsers can consume hundreds of megabytes just for a single tab.
- **Window Management**: Browsers are designed for documents, not for simulating mobile device windows. Getting a mobile-sized, borderless preview often requires manual window resizing or debugger tools.
- **Context Switching**: Interacting with terminal-based hot reload while using a browser window can be clunky.

## The solution: `flutterff`

`flutterff` provides a **native Linux container** for your Flutter application.

### 1. Directly Native
By using **GTK 3** and **WebKit2** (the same engine behind Safari/Gnome Web) directly via Python, `flutterff` creates a window that is exactly the size you need, without browser tabs, URLs, or sidebars.

### 2. Tailored for Development
It is not a general-purpose browser. It is a development tool that knows how to:
- Find your Flutter server URL automatically.
- Pass "r" and "R" keys to the Flutter process.
- Capture console logs from the JavaScript environment and pipe them directly to your terminal.

### 3. Integrated Workflow
With `flutterff`, your mobile preview feels like a native desktop app. It's draggable, resizable, and has development controls (Hot Reload, Screenshots) right in the title bar.

## Who is it for?

- **Linux-based Flutter Developers**: Who want a lightweight alternative to Chrome for web development.
- **Mobile-First Devs**: Who need a persistent, mobile-aspect-ratio window for their UI work.
- **Resource-Constrained Environments**: Developers on machines where every megabyte of RAM counts.
