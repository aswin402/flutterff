# Installation Guide

`flutterff` provides automated scripts for easy installation and updates on Linux.

## 📥 First Time Installation

To install `flutterff` globally for your user:

1.  **Clone the repository** (if you haven't already).
2.  **Run the setup script**:
    ```bash
    bash setup.sh
    ```

### What `setup.sh` does:

- **Dependency Check**: Verifies that `uv`, `flutter`, and `WebKitGTK` are installed on your system.
- **Auto-Install**: On supported systems (Ubuntu/Debian), it will offer to install missing GTK/WebKit libraries via `sudo apt`.
- **Directory Setup**: Ensures `~/.local/bin` exists in your home directory.
- **Script Deployment**: Copies `flutterff.py` to `~/.local/bin/flutterff` and makes it executable.
- **PATH Verification**: Checks if `~/.local/bin` is in your system PATH and provides instructions if it is missing.
- **Environment Pre-warming**: Runs `uv` once to ensure the environment is ready for first use.

## 🔄 Updating flutterff

If you make manual changes to `flutterff.py` in your local repository or pull a new version from Git, you can push those changes to your global installation:

```bash
bash update.sh
```

### What `update.sh` does:

- **Version Detection**: Shows the current installed version vs. the new source version.
- **Automatic Backup**: Saves a backup of your current installation to `~/.local/bin/flutterff.bak`.
- **Safe Overwrite**: Replaces the old binary with the new script.
- **Cache Refresh**: Re-warms the `uv` cache to ensure smooth execution.

## 🛠️ Manual Installation (Optional)

If you prefer not to use the scripts, you can install it manually:

1.  Copy `flutterff.py` to a directory in your PATH (e.g., `/usr/local/bin` or `~/.local/bin`).
2.  Rename it to `flutterff`.
3.  Ensure it has execute permissions: `chmod +x flutterff`.

## 🗑️ Uninstallation

To remove `flutterff`, simply delete the binary and the backup:

```bash
rm ~/.local/bin/flutterff ~/.local/bin/flutterff.bak
```
