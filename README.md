# Finance Desktop Widget

A lightweight, always-on-top desktop finance widget for Linux and Windows that displays live market data for indices, stocks, commodities, and forex, with tray integration, drag-reorder, configurable refresh intervals, and persistent settings.

Designed for users who want instant market visibility without opening a browser.

---

## Features

- Live market data
  - Indices
  - Stocks
  - Commodities
  - Forex
- Configurable refresh interval
  - 30s, 60s, 2m, 3m, 5m
- Drag and reorder symbols
  - Reorder symbols inside each panel
  - Order persists across restarts
- Desktop widget
  - Frameless and resizable
  - Clean, minimal UI
- System tray integration
  - Show or hide widget
  - Full right-click menu in tray
  - Run on startup toggle
- Persistent settings
  - Window position and size
  - Panel visibility
  - Symbol order
  - Refresh interval
  - Autostart preference
- Live footer status
  - Displays data freshness as `Updated 12s ago    vX.Y.Z`
- Consistent theming
  - Unified look across widget, menus, and tray

---

## Screenshots

<img width="402" height="649" alt="image" src="https://github.com/user-attachments/assets/c95aa3b9-6909-4aaa-9df7-13206a44c73e" />
<img width="395" height="661" alt="image" src="https://github.com/user-attachments/assets/5b85c3b7-ac96-4d3b-b64f-e8d5f3cce8d2" />
<img width="405" height="544" alt="image" src="https://github.com/user-attachments/assets/6874acf2-968e-49c3-9731-50e55d19946d" />

---

## Requirements

- OS
  - Linux
  - Windows
- Python 3.8+
- Desktop environment
  - Linux: GNOME, KDE, XFCE, or another environment with tray support
  - Windows: standard desktop session with system tray support

### Python dependencies

- PyQt5
- requests
- yfinance

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/fuzonmedia/finance-desktop-widget.git
cd finance-desktop-widget
```

### 2. Install on Linux

Run the Linux installer:

```bash
chmod +x install_finance_widget.sh
./install_finance_widget.sh
```

This will:

- Install system and Python dependencies
- Start the widget immediately
- Add it to Linux startup

### 3. Install on Windows

Install Python for Windows first if it is not already installed, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_finance_widget.ps1
```

This will:

- Create a local virtual environment in `.venv`
- Install Python dependencies
- Start the widget immediately
- Add it to Windows login startup

---

## Run Manually

### Linux

```bash
python3 finance_widget.py
```

### Windows

If you used the bundled local virtual environment:

```powershell
.\.venv\Scripts\python.exe .\finance_widget.py
```

---

## Usage

### Widget right-click

- Toggle panels: Indices, Stocks, Commodities, Forex
- Change refresh interval
- Exit widget

### Drag and reorder

- Click and drag a symbol within a panel
- Order is saved automatically

### System tray

- Right-click tray icon for the full menu
- Toggle `Run on Startup`
- Show or hide the widget

---

## Configuration Files

All user data is stored locally.

### Linux

```text
~/.config/finance_widget/
|-- settings.json
`-- symbols.json
```

### Windows

```text
%APPDATA%\finance_widget\
|-- settings.json
`-- symbols.json
```

`settings.json` stores window position, panel visibility, refresh interval, and autostart preference.

`symbols.json` stores tracked symbols and their saved order.

---

## Startup Behavior

- Linux autostart uses `~/.config/autostart/finance-widget.desktop`
- Windows autostart uses `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\finance-widget.cmd`
- The tray menu can enable or disable startup on both platforms

---

## Design Notes

- Uses Qt native layouts
- Tray menu and widget menu share the same logic
- UI timers are separated from data fetch logic
- Thread-safe UI updates use Qt signals
- Settings loading is tolerant of empty or malformed local config files

---

## Known Limitations

- Market data depends on Yahoo Finance and NSE availability
- Some commodities may not update outside trading hours
- Tray behavior depends on the Linux desktop environment or Windows shell

---

## License

MIT License, free for personal and commercial use.

---

## Credits

Designed and developed by **Niladri Dey**.
