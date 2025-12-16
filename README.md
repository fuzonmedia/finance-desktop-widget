# 📊 Finance Desktop Widget (Linux)

A lightweight, always-on-top **desktop finance widget** for Linux that displays **live market data** for indices, stocks, commodities, and forex — with **tray integration, drag‑reorder, configurable refresh intervals**, and **persistent settings**.

Designed for users who want **instant market visibility without opening a browser**.

---

## ✨ Features

- 📈 **Live market data**
  - Indices
  - Stocks
  - Commodities
  - Forex
- ⏱ **Configurable refresh interval**
  - 30s, 60s, 2m, 3m, 5m
- 🔄 **Drag & reorder symbols**
  - Reorder symbols **inside each panel**
  - Order persists across restarts
- 🖥 **Desktop widget**
  - Frameless and resizable
  - Clean, minimal UI
- 📌 **System tray integration**
  - Show / Hide widget
  - Full right‑click menu in tray
  - Run on startup toggle
- 💾 **Persistent settings**
  - Window position & size
  - Panel visibility
  - Symbol order
  - Refresh interval
  - Autostart preference
- 🕒 **Live footer status**
  - Displays data freshness  
    `Updated 12s ago    vX.Y.Z`
- 🎨 **Consistent theming**
  - Unified look across widget, menus, and tray

---

## 🖼 Screenshots

_Add screenshots for better visibility on GitHub_



---

## 🛠 Requirements

- **OS:** Linux (tested on Ubuntu 22.04+)
- **Python:** 3.8+
- **Desktop Environment:** GNOME / KDE / XFCE (tray supported)

### Python dependencies
- PyQt5
- requests
- yfinance

---

## 🚀 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/fuzonmedia/finance-desktop-widget.git
cd finance-desktop-widget
```

### 2️⃣ Run the installer

```bash
chmod +x install_finance_widget.sh
./install_finance_widget.sh
```

This will:
- Install system and Python dependencies
- Start the widget immediately
- Add it to system startup

---

## ▶ Run Manually

```bash
python3 finance_widget.py
```

---

## 🖱 Usage

### Widget right‑click
- Toggle panels (Indices / Stocks / Commodities / Forex)
- Change refresh interval
- Exit widget

### Drag & reorder
- Click and drag a symbol **within a panel**
- Order is saved automatically

### System tray
- Right‑click tray icon for full menu
- Toggle **Run on Startup**
- Show / Hide widget

---

## ⚙ Configuration Files

All user data is stored locally:

```
~/.config/finance_widget/
├── settings.json   # window, panels, refresh, autostart
└── symbols.json    # symbols and their order
```

Safe to back up or edit manually.

---

## 🧠 Design Notes

- Uses Qt native layouts (no scroll hacks)
- Tray menu and widget menu share the same logic
- UI timers are separated from data fetch logic
- Thread‑safe UI updates using Qt signals

---

## 🧩 Known Limitations

- Market data depends on Yahoo Finance availability
- Some commodities may not update outside trading hours
- Tray behavior depends on Linux desktop environment

---

## License

MIT License — free for personal and commercial use.

---

## Credits

Designed & developed by **Niladri Dey**.
