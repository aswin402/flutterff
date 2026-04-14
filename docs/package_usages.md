# Packages & Technologies

`flutterff` relies on a mix of standard Python libraries and Linux system packages.

## 🐍 Python Standard Library

The following modules enable the core logic without external pip dependencies:

- **`subprocess`**: Used to launch the `flutter` command, capture output, and inject keys into `stdin`.
- **`threading`**: Allows monitoring stdout/stderr without blocking the main GTK UI thread.
- **`socket`**: Used to check for internet connectivity and find available ports.
- **`argparse`**: Powering the CLI interface and flags.
- **`signal`**: Ensures that cutting the tool with `Ctrl + C` properly cleans up the child processes.
- **`re`**: Used for cleaning ANSI codes from logs and finding URLs in the text stream.

## 🦊 PyGObject (gi)

The "Native" part of `flutterff` comes from the GObject Introspection bindings:

- **`Gtk`**: The toolkit used to build the window, header bar, and menus.
- **`WebKit2`**: The core engine that renders the Flutter web application.
- **`Gdk` & `GdkPixbuf`**: Used for window management (resizing) and saving screenshots.
- **`GLib`**: Provides the main loop and timeout functions for asynchronous operations.

## 📦 System Dependencies

On Linux, these packages must be installed for the `gi` bindings to work:

- **`python3-gi`**: The bridge between Python and GObject.
- **`gir1.2-gtk-3.0`**: The GTK 3 library.
- **`gir1.2-webkit2-4.1`** (or `4.0`): The WebKit engine.

## 🛠️ Build & Environment Tools

- **`uv`**: Used for running the script with managed dependencies and pre-warming the environment.
- **`bash`**: Powering the `setup.sh` and `update.sh` automation scripts.
