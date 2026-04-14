# Examples & Workflows

Here are common ways to use `flutterff` in your daily development.

## 📱 Testing Different Devices

Launch your app specifically for an iPhone 14 Pro aspect ratio:
```bash
flutterff --size iphone
```

Need to test a smaller Android device?
```bash
flutterff --size mobile-small
```

Testing a tablet layout:
```bash
flutterff --size tablet
```

## 🌐 Custom Ports

If you have multiple Flutter apps running, or your port 8080 is occupied:
```bash
flutterff --port 3000
```
`flutterff` will automatically instruct Flutter to use that port and then point the native window to it.

## 📈 Performance Profiling

Run your app in "Profile Mode" to see how it performs without the debug overhead. This is useful for checking animations and scroll performance.
```bash
flutterff --profile
```

## ✈️ Developing Offline

If you're on a plane or have spotting internet, bypass the network checks:
```bash
flutterff --offline
```
This forces Flutter to skip `pub get` checks and prevents it from trying to load assets from the Google CDN.

## 📸 Capturing your UI

While running, click the **Camera Icon** in the header bar.
- The screenshot will be saved as `screenshots/screenshot_YYYYMMDD_HHMMSS.png`.
- This is perfect for documenting PRs or sharing progress with designers.

## 🛠️ Adding a New Preset

Don't see your favorite device? You can launch with a custom size immediately:
```bash
flutterff --size 430x932
```
To make this permanent, see the [Modification Guide](modification.md).
