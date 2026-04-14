# Developer Setup

If you want to contribute to `flutterff` or run it from source, follow this guide.

## 1. System Requirements

Ensure you are on a Linux distribution with GTK support (Ubuntu, Fedora, Arch, etc.).

Install the development libraries:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 python3-gi-cairo
```

**Fedora:**
```bash
sudo dnf install python3-gobject webkit2gtk4.1
```

**Arch Linux:**
```bash
sudo pacman -S python-gobject webkit2gtk-4.1
```

## 2. Python Environment

`flutterff` uses `uv` for managing dependencies and running scripts reliably.

1.  **Install `uv`**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Verify path**:
    Ensure `uv` is in your PATH.

## 3. Flutter Requirements

You must have Flutter installed and configured for web development:
```bash
flutter doctor
flutter config --enable-web
```

## 4. Running from Source

You can run `flutterff` directly without installing it:
```bash
python3 flutterff.py
# OR using uv
uv run flutterff.py
```

## 5. Development Workflow

1.  Make changes to `flutterff.py`.
2.  Test your changes by running the script locally.
3.  Once satisfied, use `bash update.sh` to update your global command.
4.  Optionally, update the version number in `flutterff.py` before updating.
