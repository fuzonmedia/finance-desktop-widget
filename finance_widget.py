#!/usr/bin/env python3
import os, sys, json, signal, requests, yfinance as yf
from pathlib import Path
from json import JSONDecodeError

from PyQt5.QtCore import Qt, QTimer, QThread, QObject, pyqtSignal, QPoint, QRect
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QMenu, QDialog, QLineEdit,
    QComboBox, QPushButton,
    QListWidget, QListWidgetItem
)

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QSystemTrayIcon, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QCursor
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QDrag
import time




# ================= DEBUG =================
DEBUG = True
def log(*a):
    if DEBUG:
        print("[DEBUG]", *a, flush=True)

# ================= THEME =================
DARK = {
    "bg": "#0f1115",
    "panel": "#1b1f27",
    "header": "#4dabf7",
    "text": "#e6e6e6",
    "up": "#00c853",
    "down": "#ff5252",
    "neutral": "#9aa0a6",
    "menu_bg": "#1e222b",
    "menu_hover": "#2a2f3a",
    "menu_border": "#333842"
}

LIGHT = {
    "bg": "#fafafa",
    "panel": "#ffffff",
    "header": "#1976d2",
    "text": "#212121",
    "up": "#2e7d32",
    "down": "#c62828",
    "neutral": "#757575",
    "menu_bg": "#ffffff",
    "menu_hover": "#e3f2fd",
    "menu_border": "#cfd8dc"
}

THEME = DARK
BASE_FONT = QFont("Sans", 9)
RESIZE_MARGIN = 14

APP_VERSION = "v1.0.1"

#================= TRAY ICON =================
def create_tray_icon():
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    p.setBrush(QColor("#4dabf7"))
    p.setPen(Qt.NoPen)
    p.drawEllipse(4, 4, 56, 56)

    p.setBrush(QColor("white"))
    p.drawRect(20, 30, 6, 18)
    p.drawRect(30, 22, 6, 26)
    p.drawRect(40, 14, 6, 34)

    p.end()
    return QIcon(pix)

#================= CONTEXT MENU STYLESHEET =================


def menu_stylesheet():
    return f"""
        QMenu {{
            background:{THEME['menu_bg']};
            border:1px solid {THEME['menu_border']};
        }}
        QMenu::item {{
            color:{THEME['text']};
            padding:4px 20px;
        }}
        QMenu::item:selected {{
            background:{THEME['menu_hover']};
        }}
    """

# ================= CONFIG =================
def get_base_dir():
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "finance_widget"
    return Path.home() / ".config" / "finance_widget"


def get_autostart_file():
    if sys.platform.startswith("win"):
        startup = (
            Path(os.environ["APPDATA"])
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )
        return startup / "finance-widget.cmd"
    autostart_dir = Path.home() / ".config" / "autostart"
    return autostart_dir / "finance-widget.desktop"


BASE_DIR = get_base_dir()
BASE_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS_FILE = BASE_DIR / "symbols.json"
SETTINGS_FILE = BASE_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "x": 200, "y": 200,
    "width": 360, "height": 520,
    "panels": {
        "indices": True,
        "stocks": True,
        "commodities": True,
        "forex": True
    },
    "autostart": True,   # ← ADD THIS FLAG
    "refresh_interval": 30   # seconds (ADD THIS)
}

# ================= AUTOSTART =================
AUTOSTART_FILE = get_autostart_file()

def enable_autostart():
    AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
    app_path = Path(__file__).resolve()

    if sys.platform.startswith("win"):
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        launcher = pythonw if pythonw.exists() else Path(sys.executable)
        AUTOSTART_FILE.write_text(
            f'@echo off\r\nstart "" "{launcher}" "{app_path}"\r\n',
            encoding="utf-8"
        )
    else:
        AUTOSTART_FILE.write_text(f"""[Desktop Entry]
Type=Application
Name=Finance Widget
Exec={sys.executable} {app_path}
X-GNOME-Autostart-enabled=true
""")

def disable_autostart():
    if AUTOSTART_FILE.exists():
        AUTOSTART_FILE.unlink()

def is_autostart_enabled():
    return AUTOSTART_FILE.exists()



# ================= SETTINGS =================

def load_settings():
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=2))
    try:
        raw = SETTINGS_FILE.read_text(encoding="utf-8-sig").strip()
        data = json.loads(raw) if raw else {}
    except (OSError, JSONDecodeError):
        data = {}
        SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=2), encoding="utf-8")
    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    merged["panels"] = {**DEFAULT_SETTINGS["panels"], **data.get("panels", {})}
    return merged

def save_settings(w, panels, autostart):
    g = w.geometry()
    SETTINGS_FILE.write_text(json.dumps({
        "x": g.x(), "y": g.y(),
        "width": g.width(), "height": g.height(),
        "panels": panels,
        "autostart": autostart,
        "refresh_interval": w.settings.get("refresh_interval", 30)
    }, indent=2))


def clamp_widget_geometry(x, y, width, height):
    app = QApplication.instance()
    if not app:
        return x, y, width, height

    point = QPoint(x, y)
    screen = app.screenAt(point) or app.primaryScreen()
    if not screen:
        return x, y, width, height

    available = screen.availableGeometry()
    min_width = 300
    min_height = 200

    width = max(min_width, min(width, available.width()))
    height = max(min_height, min(height, available.height()))

    max_x = available.x() + max(0, available.width() - width)
    max_y = available.y() + max(0, available.height() - height)
    x = min(max(x, available.x()), max_x)
    y = min(max(y, available.y()), max_y)

    return x, y, width, height

# ================= SYMBOLS =================
DEFAULT_SYMBOLS = {
    "indices": [{"name": "NIFTY 50", "symbol": "NIFTY 50", "provider": "nse_index"}],
    "stocks": [
        {"name": "RELIANCE", "symbol": "RELIANCE", "provider": "nse_stock"},
        {"name": "TCS", "symbol": "TCS", "provider": "nse_stock"}
    ],
    "commodities": [{"name": "GOLD", "symbol": "GC=F", "provider": "yahoo"}],
    "forex": [{"name": "USD/INR", "symbol": "USDINR=X", "provider": "yahoo"}]
}

def load_symbols():
    if not SYMBOLS_FILE.exists():
        SYMBOLS_FILE.write_text(json.dumps(DEFAULT_SYMBOLS, indent=2))
    try:
        raw = SYMBOLS_FILE.read_text(encoding="utf-8-sig").strip()
        return json.loads(raw) if raw else DEFAULT_SYMBOLS
    except (OSError, JSONDecodeError):
        SYMBOLS_FILE.write_text(json.dumps(DEFAULT_SYMBOLS, indent=2), encoding="utf-8")
        return DEFAULT_SYMBOLS

def save_symbols(s):
    SYMBOLS_FILE.write_text(json.dumps(s, indent=2))

def infer_provider(symbol, name):
    symbol = symbol.strip()
    name = name.strip()
    if " " in symbol and name.startswith("NIFTY"):
        return "nse_index"
    if symbol.isupper() and "." not in symbol and "=" not in symbol:
        return "nse_stock"
    return "yahoo"


def india_yahoo_symbol(sym):
    sym = sym.strip()
    return sym if "." in sym or "=" in sym else f"{sym}.NS"

# ================= DATA =================
NSE = requests.Session()
NSE.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/"
})

def fetch_nse_index(name):
    name = name.strip()
    try:
        NSE.get("https://www.nseindia.com", timeout=8)
        r = NSE.get("https://www.nseindia.com/api/allIndices", timeout=8)
        for i in r.json().get("data", []):
            if i.get("index") == name:
                return (
                    float(i.get("last", 0)),
                    float(i.get("change") or i.get("variation") or 0),
                    float(i.get("percentChange", 0))
                )
    except Exception as e:
        log("NSE INDEX FALLBACK:", name, e)

    if " " not in name:
        return fetch_yahoo(india_yahoo_symbol(name))
    return None, None, None

def fetch_nse_stock(sym):
    sym = sym.strip()
    try:
        NSE.get("https://www.nseindia.com", timeout=8)
        r = NSE.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=8)
        p = r.json().get("priceInfo")
        if p:
            return float(p["lastPrice"]), float(p["change"]), float(p["pChange"])
    except Exception as e:
        log("NSE STOCK FALLBACK:", sym, e)

    return fetch_yahoo(india_yahoo_symbol(sym))

def fetch_yahoo(sym):
    t = yf.Ticker(sym)

    # ---- Primary: 2-day candle (normal trading) ----
    try:
        h = t.history(period="2d")
        if not h.empty and len(h) >= 2:
            last, prev = h["Close"].iloc[-1], h["Close"].iloc[-2]
            ch = last - prev
            return float(last), float(ch), (ch / prev) * 100
    except Exception:
        pass

    # ---- Secondary: fast_info (may be empty for futures) ----
    try:
        fi = t.fast_info
        last = fi.get("last_price")
        prev = fi.get("previous_close")
        if last is not None and prev:
            ch = last - prev
            return float(last), float(ch), (ch / prev) * 100
    except Exception:
        pass

    # ---- FINAL fallback: 1-minute quote snapshot (MOST RELIABLE) ----
    try:
        h = t.history(period="1d", interval="1m", prepost=True)
        if not h.empty:
            last = h["Close"].iloc[-1]
            prev = h["Close"].iloc[0]
            ch = last - prev
            return float(last), float(ch), (ch / prev) * 100
    except Exception:
        pass

    return None, None, None



# ================= WORKER =================
class FetchWorker(QObject):
    result = pyqtSignal(dict)
    def fetch(self, symbols):
        data = {}
        for items in symbols.values():
            for s in items:
                try:
                    if s["provider"] == "nse_index":
                        data[s["name"]] = fetch_nse_index(s["symbol"])
                    elif s["provider"] == "nse_stock":
                        data[s["name"]] = fetch_nse_stock(s["symbol"])
                    else:
                        data[s["name"]] = fetch_yahoo(s["symbol"])
                except Exception as e:
                    log("FETCH ERROR:", e)
        self.result.emit(data)

# ================= UI =================
class Row(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = QLabel(name)
        self.price = QLabel("--")
        self.change = QLabel("--")

        self.name.setFont(BASE_FONT)
        self.price.setFont(QFont("Sans", 9, QFont.Bold))
        self.change.setFont(BASE_FONT)

        l = QHBoxLayout(self)
        l.setContentsMargins(6, 1, 6, 1)
        l.addWidget(self.name, 1)
        l.addWidget(self.price)
        l.addWidget(self.change)

    def apply_theme(self):
        self.setStyleSheet(f"color:{THEME['text']}")

    def update_value(self, p, ch, pct):
        if p is None:
            self.price.setText("--")
            self.change.setText("--")
            self.change.setStyleSheet(f"color:{THEME['neutral']}")
            return
        self.price.setText(f"{p:.2f}")
        self.change.setText(f"{pct:+.2f}%")
        self.change.setStyleSheet(
            f"color:{THEME['up'] if pct >= 0 else THEME['down']}"
        )

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start = e.pos()

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton):
            return
        if (e.pos() - self._drag_start).manhattanLength() < 8:
            return

        mime = QMimeData()
        mime.setText(self.name.text())

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.MoveAction)


class Panel(QFrame):
    def __init__(self, title, category, parent):
        super().__init__(parent)
        self.category = category
        self.rows = []

        outer = QVBoxLayout(self)
        outer.setSpacing(4)
        outer.setContentsMargins(6, 4, 6, 4)

        self.header = QLabel(title)
        self.header.setFont(QFont("Sans", 10, QFont.Bold))
        outer.addWidget(self.header)

        self.container = QWidget(self)
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setSpacing(2)
        self.vbox.setContentsMargins(0, 0, 0, 0)

        self.setAcceptDrops(True)

        outer.addWidget(self.container)

        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            QSizePolicy.Maximum
        )

        self.apply_theme()

    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e):
        name = e.mimeData().text()

        src = next((r for r in self.rows if r.name.text() == name), None)
        if not src:
            return

        pos = e.pos().y()

        for i, r in enumerate(self.rows):
            if r is src:
                continue
            if r.y() > pos:
                self._move_row(src, i)
                e.acceptProposedAction()
                return

        self._move_row(src, len(self.rows))
        e.acceptProposedAction()


    def _move_row(self, row, index):
        self.vbox.removeWidget(row)
        self.rows.remove(row)

        self.rows.insert(index, row)
        self.vbox.insertWidget(index, row)

        self.parent().update_symbol_order(
            self.category,
            [r.name.text() for r in self.rows]
        )

    
    def apply_theme(self):
        self.setStyleSheet(f"background:{THEME['panel']}; border-radius:6px;")
        self.header.setStyleSheet(f"color:{THEME['header']}")

        for row in self.rows:
            row.apply_theme()


    def _update_list_height(self):
        self.list.updateGeometry()
        self.list.viewport().update()

        if self.list.count() == 0:
            self.list.setFixedHeight(0)
            return

        total = 0
        for i in range(self.list.count()):
            total += self.list.sizeHintForRow(i)

        total += self.list.spacing() * (self.list.count() - 1)

        m = self.list.contentsMargins()
        total += m.top() + m.bottom()
        total += 2 * self.list.frameWidth()

        self.list.setFixedHeight(total)



    def on_reorder(self):
        ordered = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            row = self.list.itemWidget(item)
            ordered.append(row.name.text())

        self.parent().update_symbol_order(self.category, ordered)
        QTimer.singleShot(0, self._update_list_height)



    
    def add_row(self, name):
        row = Row(name)
        row.apply_theme()
        self.vbox.addWidget(row)
        self.rows.append(row)

    def remove_row(self, name):
        for r in self.rows:
            if r.name.text() == name:
                self.vbox.removeWidget(r)
                self.rows.remove(r)
                r.deleteLater()
                return



    def update(self, data):
        for r in self.rows:
            if r.name.text() in data:
                r.update_value(*data[r.name.text()])



class NoScrollList(QListWidget):
    def wheelEvent(self, event):
        event.ignore()


# ================= ADD / REMOVE DIALOGS =================
class AddSymbolDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent, flags=Qt.FramelessWindowHint)
        self.setStyleSheet(f"background:{THEME['panel']}; color:{THEME['text']}")
        l = QVBoxLayout(self)

        header = QHBoxLayout()
        lbl = QLabel("Add Symbol")
        lbl.setFont(QFont("Sans", 10, QFont.Bold))
        close = QPushButton("✕")
        close.setFixedWidth(28)
        close.clicked.connect(self.reject)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(close)

        self.name = QLineEdit()
        self.symbol = QLineEdit()
        self.category = QComboBox()
        self.category.addItems(["indices", "stocks", "commodities", "forex"])

        btn = QPushButton("Add")
        btn.clicked.connect(self.accept)

        l.addLayout(header)
        for w in (QLabel("Name"), self.name,
                  QLabel("Symbol"), self.symbol,
                  QLabel("Category"), self.category, btn):
            l.addWidget(w)

class RemoveSymbolDialog(QDialog):
    def __init__(self, parent, symbols):
        super().__init__(parent, flags=Qt.FramelessWindowHint)
        self.setStyleSheet(f"background:{THEME['panel']}; color:{THEME['text']}")
        l = QVBoxLayout(self)

        header = QHBoxLayout()
        lbl = QLabel("Remove Symbol")
        lbl.setFont(QFont("Sans", 10, QFont.Bold))
        close = QPushButton("✕")
        close.setFixedWidth(28)
        close.clicked.connect(self.reject)
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(close)

        self.combo = QComboBox()
        self.map = {}
        for cat, items in symbols.items():
            for s in items:
                key = f"{s['name']} ({cat})"
                self.map[key] = (cat, s)
                self.combo.addItem(key)

        btn = QPushButton("Remove")
        btn.clicked.connect(self.accept)

        l.addLayout(header)
        l.addWidget(self.combo)
        l.addWidget(btn)

# ================= MAIN WIDGET =================
class FinanceWidget(QWidget):
    def __init__(self):
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint)

        self.symbols = load_symbols()
        self.settings = load_settings()
        self.last_refresh_ts = None

        # Apply autostart based on saved settings
        if self.settings.get("autostart", True):
            enable_autostart()
        else:
            disable_autostart()


        self._drag_pos = None
        self._resizing = False
        self.setMouseTracking(True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)



        self.panels = {
            "indices": Panel("Indices", "indices", self),
            "stocks": Panel("Stocks", "stocks", self),
            "commodities": Panel("Commodities", "commodities", self),
            "forex": Panel("Forex", "forex", self),
        }

        for p in self.panels.values():
            self.layout.addWidget(p,0)

        for cat, items in self.symbols.items():
            for s in items:
                self.panels[cat].add_row(s["name"])

        # ---- Footer (Version label pinned bottom-right) ----
        footer = QWidget(self)

        footer.setSizePolicy(
            footer.sizePolicy().horizontalPolicy(),
            QSizePolicy.Fixed
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        self.footer_label = QLabel(self)
        self.footer_label.setFont(QFont("Sans", 8))
        self.footer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.footer_label.setText("Updated --    " + APP_VERSION)

        footer_layout.addWidget(self.footer_label)

        self.layout.addWidget(footer,0)

       


        
        self.thread = QThread(self)
        self.worker = FetchWorker()
        self.worker.moveToThread(self.thread)
        self.worker.result.connect(self.update_ui)
        self.thread.start()

        self.timer = QTimer()

        self.footer_timer = QTimer(self)
        self.footer_timer.timeout.connect(self.update_footer_time)
        self.footer_timer.start(1000)


        self.timer.timeout.connect(lambda: self.worker.fetch(self.symbols))
        self.refresh_interval = self.settings.get("refresh_interval", 30)
        self.timer.start(self.refresh_interval * 1000)

        self.worker.fetch(self.symbols)

        x, y, width, height = clamp_widget_geometry(
            self.settings["x"],
            self.settings["y"],
            self.settings["width"],
            self.settings["height"]
        )
        self.setGeometry(x, y, width, height)

        self.apply_theme()
        self.apply_panel_visibility()

        # ---- System Tray (final, stable) ----
        self.tray = QSystemTrayIcon(create_tray_icon(), self)
        self.tray.setToolTip(f"Finance Widget {APP_VERSION}")

        # Build tray menu dynamically when opened
        tray_menu = QMenu(self)
        tray_menu.setStyleSheet(menu_stylesheet())

        def rebuild_tray_menu():
            tray_menu.clear()
            tray_menu.setStyleSheet(menu_stylesheet())

            # Autostart toggle (tray-only)
            autostart_action = QAction("Run on Startup", self)
            autostart_action.setCheckable(True)
            autostart_action.setChecked(self.settings.get("autostart", True))
            autostart_action.triggered.connect(self.toggle_autostart)
            tray_menu.addAction(autostart_action)

            tray_menu.addSeparator()

            # Reuse widget context menu items
            ctx = self.build_context_menu()
            for act in ctx.actions():
                tray_menu.addAction(act)

        # Rebuild menu every time before showing
        tray_menu.aboutToShow.connect(rebuild_tray_menu)

        self.tray.setContextMenu(tray_menu)
        self.tray.show()


    def update_footer_time(self):
        if not self.last_refresh_ts:
            self.footer_label.setText("Updated --    " + APP_VERSION)
            return

        delta = int(time.time() - self.last_refresh_ts)

        if delta < 60:
            txt = f"Updated {delta}s ago"
        else:
            txt = f"Updated {delta//60}m {delta%60}s ago"

        self.footer_label.setText(f"{txt}    {APP_VERSION}")


    def set_refresh_interval(self, seconds):
        self.refresh_interval = seconds
        self.settings["refresh_interval"] = seconds

        self.timer.stop()
        self.timer.start(seconds * 1000)

        save_settings(
            self,
            self.settings["panels"],
            self.settings.get("autostart", True)
        )

    def update_symbol_order(self, category, ordered_names):
        current = self.symbols.get(category, [])
        mapping = {s["name"]: s for s in current}

        self.symbols[category] = [
            mapping[name] for name in ordered_names if name in mapping
        ]

        save_symbols(self.symbols)


    def toggle_autostart(self, checked):
        self.settings["autostart"] = checked
        if checked:
            enable_autostart()
        else:
            disable_autostart()

        save_settings(
            self,
            self.settings["panels"],
            self.settings.get("autostart", True)
        )
    

    def apply_theme(self):
        self.setStyleSheet(f"background:{THEME['bg']}")
        for p in self.panels.values():
            p.apply_theme()
        if hasattr(self, "footer_label"):
            self.footer_label.setStyleSheet(
                f"color:{THEME['neutral']}; padding-right:4px;"
            )


    def apply_panel_visibility(self):
        for k, v in self.settings["panels"].items():
            self.panels[k].setVisible(v)

    def update_ui(self, data):
        self.last_refresh_ts = time.time()   # ← ADD THIS LINE
        for p in self.panels.values():
            p.update(data)

    # -------- MOVE / RESIZE --------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            if self._in_resize_zone(e.pos()):
                self._resizing = True
            else:
                self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._resizing:
            self.resize(max(300, e.pos().x()), max(200, e.pos().y()))
        elif self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)
        else:
            self.setCursor(
                Qt.SizeFDiagCursor if self._in_resize_zone(e.pos())
                else Qt.ArrowCursor
            )

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self._resizing = False
        save_settings(self,self.settings["panels"],self.settings.get("autostart", True))

    def _in_resize_zone(self, pos):
        return (
            pos.x() > self.width() - RESIZE_MARGIN and
            pos.y() > self.height() - RESIZE_MARGIN
        )

    # -------- CONTEXT MENU --------
    def build_context_menu(self):
        m = QMenu(self)
        m.setStyleSheet(menu_stylesheet())

        for key in self.panels:
            act = m.addAction(key.title())
            act.setCheckable(True)
            act.setChecked(self.settings["panels"][key])
            act.triggered.connect(lambda _, k=key: self.toggle_panel(k))

        m.addSeparator()
        m.addAction("Add Symbol", self.add_symbol)
        m.addAction("Remove Symbol", self.remove_symbol)
        m.addSeparator()
        m.addAction("Toggle Theme", self.toggle_theme)
        m.addSeparator()

        # ---- Refresh Interval submenu ----
        refresh_menu = QMenu("Refresh Interval", self)
        refresh_menu.setStyleSheet(menu_stylesheet())


        intervals = [
            ("30s", 30),
            ("60s", 60),
            ("2m", 120),
            ("3m", 180),
            ("5m", 300),
        ]

        for label, seconds in intervals:
            act = refresh_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(self.settings.get("refresh_interval", 30) == seconds)
            act.triggered.connect(lambda _, s=seconds: self.set_refresh_interval(s))

        m.addMenu(refresh_menu)
        m.addSeparator()
        m.addAction("Exit", QApplication.quit)

        return m

    def contextMenuEvent(self, e):
        self.build_context_menu().exec_(e.globalPos())
    


    def toggle_panel(self, key):
        self.settings["panels"][key] = not self.settings["panels"][key]
        self.panels[key].setVisible(self.settings["panels"][key])
        save_settings(self, self.settings["panels"], self.settings.get("autostart", True))

    def add_symbol(self):
        d = AddSymbolDialog(self)
        if d.exec_():
            entry = {
                "name": d.name.text(),
                "symbol": d.symbol.text(),
                "provider": infer_provider(d.symbol.text(), d.name.text())
            }
            cat = d.category.currentText()
            self.symbols[cat].append(entry)
            save_symbols(self.symbols)
            self.panels[cat].add_row(entry["name"])
            self.worker.fetch(self.symbols)

    def remove_symbol(self):
        d = RemoveSymbolDialog(self, self.symbols)
        if d.exec_():
            cat, sym = d.map[d.combo.currentText()]
            self.symbols[cat].remove(sym)
            save_symbols(self.symbols)
            self.panels[cat].remove_row(sym["name"])
            self.worker.fetch(self.symbols)

    def toggle_theme(self):
        global THEME
        THEME = LIGHT if THEME == DARK else DARK
        self.apply_theme()

    def closeEvent(self, e):
        save_settings(self,self.settings["panels"],self.settings.get("autostart", True))

        self.thread.quit()
        self.thread.wait()
        super().closeEvent(e)

# ================= ENTRY =================
def main():
    if sys.platform.startswith("win"):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    if not sys.platform.startswith("win"):
        signal.signal(signal.SIGINT, lambda *_: QApplication.quit())
    w = FinanceWidget()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
