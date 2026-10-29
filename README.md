<div align="center">

# 🎯 VAI — Valorant Agent Instalock Helper

**A zero-overhead, 100% Vanguard-compliant passive visual alignment overlay for *Valorant*.**

[![Release](https://img.shields.io/github/v/release/aaynu/VAI?style=for-the-badge&color=blue)](https://github.com/aaynu/VAI/releases)
[![Vanguard Safe](https://img.shields.io/badge/Vanguard-100%25%20Safe-brightgreen?style=for-the-badge)](https://github.com/aaynu/VAI#-vanguard-anti-cheat-safety-guarantee)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=for-the-badge&logo=windows)](https://github.com/aaynu/VAI)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python)](https://github.com/aaynu/VAI)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

<p align="center">
  <b>Pre-aim your physical mouse cursor at the exact Agent Select coordinates before the character grid even loads.</b><br/>
  No memory tampering. No botting. No automated clicks. Just crisp visual reticles rendered on top of Windows.
</p>

[📥 Download Installer (`setup.exe`)](https://github.com/aaynu/VAI/releases/latest) • [🎮 Quick Start Guide](#-quick-start-for-everyone-non-technical-users) • [⌨️ Hotkeys](#-hotkey-cheatsheet) • [🛡️ Anti-Cheat Safety](#-vanguard-anti-cheat-safety-guarantee)

---

</div>

## 💡 What is VAI?

In *Valorant*, locking your favorite agent often comes down to milliseconds. Traditional "instalock bots" inject into game memory or simulate fake mouse clicks, which gets accounts permanently banned by **Riot Vanguard**.

**VAI (Valorant Agent Instalock Helper)** takes a completely legal, passive approach:
- It renders a subtle, translucent reticle directly on your screen (Role Filter Tab, Agent Portrait Slot, and Lock-In button).
- You rest your physical mouse over the waypoint before the agent select screen even finishes loading.
- As soon as the lobby pops, your cursor is already in the exact pixel position — you simply click once and lock your agent before anyone else has even moved their mouse!

```
     ┌────────────────────────────────────────────────────────┐
     │  1. Rest cursor on [Role Tab] or [Agent Reticle]       │
     │  2. Match loads -> Click Agent Portrait Slot           │
     │  3. Flick to [Lock-In Reticle] -> Click Lock           │
     │  => Instant lock in < 0.2s without risky scripts!     │
     └────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start for Everyone (Non-Technical Users)

You do **not** need to know any programming, terminal commands, or Python to use VAI.

### 1. Download & Install
1. Go to the [**Latest Releases Page**](https://github.com/aaynu/VAI/releases/latest).
2. Under **Assets**, click to download **`VAI-Setup-v1.0.0.exe`**.
3. Double-click the downloaded setup file. Follow the simple on-screen wizard:
   - Choose whether you want a Desktop shortcut.
   - Click **Next** and **Install**.
4. Click **Finish** to launch **VAI**!

*(Prefer a portable version without installation? You can also download the standalone **`VAI.exe`** directly from Releases!)*

### 2. Using VAI in Valorant
1. Launch **VAI**. You will see subtle reticles appear on your primary screen.
2. Launch **Valorant** (Windowed Fullscreen or Borderless recommended).
3. Queue into a match:
   - Use `Ctrl + Shift + F10` to cycle between your saved agent presets (e.g. Jett, Clove, Reyna).
   - Place your real mouse cursor directly over the reticle.
   - When the agent select screen appears, click your agent and then the lock-in marker!
4. Once locked in, press `Ctrl + Shift + F8` to hide the overlay during the game for zero distraction and full performance.

---

## ⌨️ Hotkey Cheatsheet

All hotkeys use `Ctrl + Shift` combinations to prevent any accidental keystrokes during gameplay:

| Hotkey | Action | Description |
| :--- | :--- | :--- |
| **`Ctrl + Shift + F8`** | **Toggle Visibility** | Hides or shows the overlay. When hidden, it completely detaches from Windows DWM for 0 input lag. |
| **`Ctrl + Shift + F9`** | **Calibration Mode** | Unlocks interactive dragging & micro-nudging so you can customize reticle positions for your resolution. |
| **`Ctrl + Shift + F10`** | **Cycle Agent Preset** | Switches between configured agent coordinates (Jett, Clove, Reyna, etc.). |
| **`Ctrl + Shift + F7`** | **Cycle Monitor** | Moves the overlay between your monitors if you have a multi-display setup. |
| **`Ctrl + Shift + R`** | **Toggle Role Waypoint** | Shows or hides the top Role Filter (Duelist/Controller/Initiator/Sentinel) waypoint. |
| **`Ctrl + Shift + Q`** | **Quit VAI** | Completely closes the overlay application. |

---

## 🎯 Reticle Calibration & Customization

Every monitor resolution or aspect ratio (16:9, 16:10, 4:3 stretched) can be easily aligned:

1. Press **`Ctrl + Shift + F9`** to enter **Calibration Mode**. The overlay will display bright dashed boxes and coordinate crosshairs.
2. **Repositioning:**
   - **Click & Drag**: Simply left-click and drag any reticle to position it over your agent slot.
   - **Micro-Nudge**: Click a reticle, then use your keyboard **Arrow Keys** for precision 1-pixel nudges (or `Shift + Arrow Keys` for 5-pixel jumps).
3. **Save**:
   - Press **`Ctrl + Shift + F9`** again to exit Calibration Mode. Your changes are automatically saved!

Configuration is saved in `%APPDATA%\VAI\overlay_config.json` (or locally if portable).

---

## 🛡️ Vanguard Anti-Cheat Safety Guarantee

We prioritize account security above everything else. Here is how VAI guarantees compliance with Riot Vanguard:

1. **Zero Process Interaction**:
   - VAI never opens a handle to `VALORANT-Win64-Shipping.exe`.
   - It never reads game memory (`ReadProcessMemory`) or injects DLLs.
   - It doesn't even know if Valorant is running — it treats the desktop just like a custom wallpaper or Discord overlay.
2. **Zero Input Automation**:
   - VAI has **NO ability to move your mouse or click for you**.
   - Contains no `SendInput`, `mouse_event`, `SetCursorPos`, or macro drivers.
   - Every action in-game is 100% human input from your own hand.
3. **No Global Keyboard/Mouse Hooks**:
   - VAI does **not** install system-wide low-level hooks (`WH_KEYBOARD_LL` or `WH_MOUSE_LL`).
   - Hotkeys use the official, native Windows `RegisterHotKey` API.
4. **Hardware Independent Flip (iFlip) Friendly**:
   - When hidden (`Ctrl+Shift+F8`), the window completely calls `ShowWindow(SW_HIDE)` to detach from Windows Desktop Window Manager (DWM). This ensures your graphics card pushes frames with **zero latency and zero FPS drop**.
5. **EcoQoS & Efficiency Core Affinity**:
   - Runs with Windows 11 `EcoQoS` power efficiency, drawing essentially 0.0% CPU and keeping your system cool for gaming.

---

## 🛠️ For Developers & Advanced Users (Running from Source)

If you prefer to run or build VAI directly from source code:

### Prerequisites
- Windows 10 or Windows 11
- Python 3.11 or newer ([python.org](https://www.python.org/downloads/))
- Git ([git-scm.com](https://git-scm.com/))

### 1. Clone & Set Up Environment
```powershell
# Clone the repository
git clone https://github.com/aaynu/VAI.git
cd VAI

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Run VAI
```powershell
# Run via module
python -m val_overlay.main

# Or via installed console script
vai
```

### 3. Run Automated Tests
```powershell
pytest -v
```

### 4. Build Standalone Installer Locally
If you have [Inno Setup 6](https://jrsoftware.org/isdl.php) installed:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```
The compiled `dist/VAI.exe` and `dist/VAI-Setup-v1.0.0.exe` will be generated in the `dist/` directory.

---

## 📁 Project Architecture

```
VAI/
├── .github/
│   └── workflows/
│       ├── release.yml       # Automated GitHub Release & installer packaging on tag
│       └── ci.yml            # Automated test verification on push/PR
├── installer/
│   └── installer.iss         # Inno Setup Windows installer compiler script
├── scripts/
│   └── build.ps1             # One-click local compilation script
├── src/
│   └── val_overlay/
│       ├── __init__.py       # Package version manifest (v1.0.0)
│       ├── main.py           # Application entrypoint & DPI-Awareness initialization
│       ├── win32_bridge.py   # ctypes Win32 API, EcoQoS, E-Core affinity & styles
│       ├── config_manager.py # Atomic configuration persistence & AppData fallback
│       ├── coordinate_engine.py # UV coordinate normalization & physical pixel math
│       ├── hotkey_filter.py  # Native Win32 WM_HOTKEY message dispatcher
│       └── overlay_window.py # High-performance QPainter transparent overlay UI
├── tests/
│   └── test_core.py          # Comprehensive test suite (UV math, config, Win32)
├── pyproject.toml            # Project packaging specification
├── requirements.txt          # Production dependencies (PySide6)
└── README.md
```

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Q: Can I get banned by Riot Games / Vanguard for using VAI?</b></summary>
<p>
<b>No.</b> VAI does not read Valorant's memory, inject any code, or automate keystrokes/clicks. It is a passive transparent desktop window, similar to a physical sticky-note placed on your monitor or crosshair software. Vanguard does not ban passive overlays.
</p>
</details>

<details>
<summary><b>Q: Does VAI affect my in-game FPS?</b></summary>
<p>
<b>No.</b> VAI uses Windows 11 EcoQoS and pins itself to efficiency cores with idle priority. When you press <code>Ctrl + Shift + F8</code> to hide the overlay during the game, the window completely detaches from the Windows DWM compositor, ensuring zero overhead.
</p>
</details>

<details>
<summary><b>Q: Can I add new Agents or support 4:3 stretched resolution?</b></summary>
<p>
<b>Yes!</b> You can customize or add presets either interactively using <code>Ctrl + Shift + F9</code>, or by editing your <code>overlay_config.json</code> file in <code>%APPDATA%\VAI</code>. VAI automatically detects your screen aspect ratio (16:9, 16:10, 4:3) and applies the correct coordinate profiles.
</p>
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Feel free to fork, customize, and contribute!
