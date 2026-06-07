English | **[中文](README_zh.md)**

# 🚄 KTMB Auto Ticket Bot v1.0

An automated ticket booking system for Malaysia's KTMB train service, supporting both **Windows** and **Linux** platforms.

Powered by Playwright browser automation to simulate real user operations — fully automated ticket monitoring, smart seat selection, form filling, instant payment, and Telegram remote control.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔄 **Smart Ticket Hunt** | Auto-refresh loop when no tickets available, with customizable interval (default 180s) |
| 📅 **Multi-Task Monitoring** | Configure multiple search tasks in config.json, monitored sequentially |
| 💺 **Smart Seat Selection** | Scans all carriages, prefers normal seats → table seats; old trains support window/forward preferences |
| 💳 **Multiple Payment Methods** | KTM Wallet (auto-deduct), DuitNow (QR code), TnG, Manual |
| 🔔 **Telegram Notifications** | Booking success, heartbeat status, crash alerts → auto push with text + screenshots |
| 📱 **Remote Control** | Control the bot via Telegram Bot commands |
| 🖥️ **Web Management Panel** | Flask backend, open `localhost:5000` in browser to configure/start/stop/view logs |
| 🛡️ **Safe Logout** | `/logout` remotely logs out safely, avoiding the 30-minute cooldown |
| 🤖 **Anti-Misfire on Boot** | Automatically clears old Telegram commands on startup to prevent stale `/logout` execution |

---

## 🚀 Quick Start (3 Steps)

### 1. Install Python

Download and install Python 3.8+: https://www.python.org/downloads/

> ⚠️ Make sure to check **"Add Python to PATH"** during installation

### 2. Run the Startup Script

**Windows:** Double-click `start_bot.bat`

**Linux:** Run `bash start_linux.sh` in terminal

The script handles everything automatically: creates virtual environment, installs dependencies, installs browser, and starts the service.

### 3. Open the Management Panel

Open **http://localhost:5000** in your browser

Fill in the web interface:
- KTMB account credentials
- Routes and dates to monitor
- Telegram Bot Token (optional, for notifications and remote control)
- Payment method

Click **Save** → **Start**, then wait for tickets 🎉

---

## 📱 Telegram Remote Commands

| Command | Description |
|---------|-------------|
| `/snap` | Capture current screen and send to your phone |
| `/snap1` | Capture screen for Bot ID=1 (used when running multiple bots) |
| `/duitnow` | Generate DuitNow payment QR code |
| `/tng` | Generate Touch 'n Go payment QR code |
| `/wallet` | Use KTM Wallet for auto-deduction |
| `/manual` | Switch to manual payment mode |
| `/logout` | Safely log out of KTMB account and shut down |
| `/logout1` | Safely log out for Bot ID=1 |

> Supports both `/snap all` (broadcast) and `/snap1` (targeted) formats

---

## 📂 Project Structure

```
├── ktmb_auto.py          # Core ticket booking engine
├── app.py                # Flask web management panel
├── config.json           # Configuration file (user-created)
├── config.example.json   # Configuration template
├── start_bot.bat         # Windows one-click startup script
├── start_linux.sh        # Linux one-click startup script
├── templates/
│   └── index.html        # Web management interface
└── static/
    └── favicon.ico       # Icon
```

---

## 🔧 Configuration Guide

### search_tasks

| Field | Description |
|-------|-------------|
| `from` / `to` | Departure / Arrival station (must match KTMB website display names) |
| `year` / `month` / `day` | Target travel date |
| `time` | Target train time, format `HH:MM` |
| `is_old_train` | Whether it's an old-style train (affects seat selection logic) |

### preferences

| Field | Description |
|-------|-------------|
| `prefer_forward` | Prefer forward-facing seats (old trains) |
| `prefer_window` | Prefer window seats (old trains) |
| `prefer_normal_seat` | Prefer normal seats (new trains) |
| `accept_table_seat` | Accept table seats when no normal seats available |

### payment_method

| Value | Description |
|-------|-------------|
| `"Command"` | Wait for Telegram command to choose payment method (recommended) |
| `"KTM Wallet"` | Auto-use KTM Wallet for deduction |
| `"DuitNow"` | Auto-generate DuitNow QR code |
| `"Manual"` | Notify user for manual payment |

### bot_settings

| Field | Description |
|-------|-------------|
| `bot_id` | Bot ID to distinguish instances when running multiple bots |
| `chrome_port` | Chrome debug port (default 9222) |
| `heartbeat_interval` | Send heartbeat notification every N cycles |
| `refresh_interval` | Seconds to wait when no tickets available (default 180) |

---

## 🔄 Ticket Flow

```
Start → Clear old TG commands → Login to KTMB → Search for trains
  ↓ No tickets
Wait N seconds → Search again (loop)
  ↓ Tickets found
Select seat → Fill passenger info → Confirm order
  ↓
[Command mode] Wait for TG command to choose payment method
[Auto mode] Execute payment directly
  ↓
Payment complete → Notify user → Program exits
```

---

## ⚠️ Disclaimer

- This project is intended for **technical exchange and personal learning** only. Do not use it for any illegal activities.
- All consequences of using this tool, including **account bans, booking failures, and financial losses**, are the sole responsibility of the user.
- This project is **not affiliated with KTMB (Keretapi Tanah Melayu Berhad)** or any official organization.
- The author is not responsible for any direct or indirect damages arising from the use of this project.

---

## 📝 License

This project is licensed under the **GNU AGPLv3 License** - see the [LICENSE](LICENSE) file for details.

**⚠️ Warning:**

Under the AGPL-3.0 license, **any modifications, derivatives, or network services based on this project must release their complete source code under the same AGPL-3.0 license.**

**🚫 The following uses are prohibited:**

- **Scalping / Ticket Reselling** — Using this project for any form of ticket scalping, reselling, or illegal trading is strictly forbidden
- **Commercial Profit** — Using this project for paid ticket booking services or any commercial operations is strictly forbidden
- **Closed-Source Modifications** — Any modified versions must be fully open-sourced to users

Violators will be subject to legal action at the author's discretion.
