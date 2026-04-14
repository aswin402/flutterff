# Modification Guide

`flutterff` is a single Python script (`flutterff.py`), making it very easy to customize.

## 📱 Adding New Device Presets

To add a new device to the dropdown menu, find the `DEVICE_PRESETS` dictionary at the top of `flutterff.py`:

```python
DEVICE_PRESETS: Dict[str, Tuple[int, int]] = {
    "mobile":       (412, 915),
    "mobile-small": (360, 800),
    "iphone":       (390, 844),
    "tablet":       (768, 1024),
    "desktop":      (1280, 800),
    # Add your own here:
    "my-device":    (430, 932), 
}
```

Once you save the file, run `bash update.sh` to push the changes to your global installation.

## 🎨 Modifying UI Colors

The terminal logs use ANSI escape codes for coloring. You can modify these in the `ansi` section:

```python
GREEN  = "\033[92m"
YELLOW = "\033[93m"
# Change these constants to match your terminal theme
```

## 🛠️ Changing Hot Reload Behavior

If you want to change the delay between triggering a hot reload and refreshing the webview, modify the `on_hot_reload` function:

```python
def on_hot_reload(_btn):
    send_flutter_key("r")
    # Change 800 (ms) to a longer/shorter delay
    GLib.timeout_add(800, reload_webview) 
```

## 🚀 Pushing Changes

After you've made modifications to `flutterff.py`:

1.  Test it locally: `python3 flutterff.py`
2.  Update the global installation: `bash update.sh`

The `update.sh` script automatically:
- Backs up your old version to `~/.local/bin/flutterff.bak`.
- Copies the new script to `~/.local/bin/flutterff`.
- Refreshes the `uv` cache.
