# Usage Guide

`flutterff` is designed to be a transparent bridge between your terminal and a native mobile-styled window.

## 🚀 Command Line Interface

Run `flutterff` from the root of your Flutter project.

### Common Commands

| Command | Description |
| :--- | :--- |
| `flutterff` | Launches with default mobile size (412×915) on port 8080. |
| `flutterff --size iphone` | Launches with iPhone 14 dimensions (390×844). |
| `flutterff --size 430x932` | Launches with a custom width and height. |
| `flutterff --port 3000` | Specifies a custom port for the Flutter web server. |
| `flutterff --profile` | Runs in Flutter's "profile" mode for performance testing. |
| `flutterff --offline` | Forces offline mode (no pub get check, no CDN resources). |

### All Flags

- `--port`, `-p`: The port to host the Flutter web server on (default: 8080).
- `--size`, `-s`: Device preset name or `WxH` format (default: `mobile`).
- `--profile`: Run in profile mode instead of debug mode.
- `--no-hot`: Disable hot reload functionality.
- `--flavor`: Specify a Flutter build flavor.
- `--list-sizes`: Show all available device presets and exit.
- `--offline`: Run with `--no-pub` and disable web resources CDN.
- `--version`: Display the version number.

## ⌨️ Terminal Shortcuts

While `flutterff` is running, you can interact with it via your terminal:

- `r`: Trigger **Hot Reload**.
- `R`: Trigger **Hot Restart**.
- `Ctrl + C`: Close the application and stop the Flutter server.

## 🦊 Header Bar Controls

The native GTK header bar provides quick access to development tools:

1.  **Size Selector (Fullscreen Icon)**: Instantly switch between presets like iPhone, Tablet, and Mobile Small.
2.  **Screenshot (Camera Icon)**: Captures the current view of your application and saves it to the `screenshots/` directory in your project.
3.  **Hot Reload (⚡ Lightning Bolt)**: Manually triggers a hot reload.
4.  **Hot Restart (Refresh Icon)**: Manually triggers a hot restart.

## 🛠️ Offline Mode

If you are developing without an internet connection, use the `--offline` flag. This passes `--no-pub` and `--no-web-resources-cdn` to the Flutter build command, preventing hangs while the tool tries to fetch resources.
