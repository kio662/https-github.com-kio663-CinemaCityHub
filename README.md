# 🎬 CinemaCityHub v3.0

**Your Ultimate Telegram Movie Filter Bot — All Features**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0-green?style=for-the-badge)](https://pyrogram.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen?style=for-the-badge&logo=mongodb)](https://mongodb.com)
[![Render](https://img.shields.io/badge/Hosted-Render-blueviolet?style=for-the-badge)](https://render.com)

---

## ✨ All Features

| Feature | Description |
|---|---|
| 🔍 Movie Search | Search by name instantly |
| 🌐 Language Filter | Tamil, Hindi, English, Telugu, Malayalam & more |
| 📽️ Quality Filter | 4K, 1080p, 720p, 480p, 360p |
| ⏳ Auto Delete | Files auto-delete after timer with countdown |
| 🔒 Force Subscribe | Users must join channel to use bot |
| 🎫 Movie Request | Users request missing movies via /request |
| 📣 Admin Broadcast | Send messages to all users at once |
| 🚫 Ban / Unban | Block and unblock users |
| 📊 Stats & Top Searches | View trending movies and usage stats |
| 🛠️ Admin Panel | Full admin dashboard with inline buttons |
| 🔝 Top Movies | Show most searched movies to users |
| 📈 Download Counter | Track how many times each file is sent |
| 🚀 Keep Alive | Self-ping every 10 min — free 24/7 hosting |

---

## 📁 Project Structure

```
CinemaCityHub/
├── bot.py              ← Main entry — all handlers registered
├── config.py           ← All environment variables
├── database.py         ← MongoDB: files, users, bans, requests, stats
├── handlers.py         ← All logic: search, admin, broadcast, ban, request
├── force_sub.py        ← Force subscribe system
├── auto_delete.py      ← Auto-delete countdown timer
├── lang_detector.py    ← Auto-detect language & quality from filename
├── keyboards.py        ← All inline keyboards including admin panel
├── keep_alive.py       ← aiohttp HTTP server for Render
├── pinger.py           ← Self-ping every 10 min
├── render.yaml         ← Render auto-deploy config
├── requirements.txt    ← Python dependencies
├── .env.example        ← Credential template
├── .gitignore          ← Protect .env from git
└── README.md
```

---

## 🚀 Deploy on Render (Free)

```bash
git clone https://github.com/YOUR_USERNAME/CinemaCityHub
cd CinemaCityHub
cp .env.example .env   # fill in credentials
pip install -r requirements.txt
python bot.py
```

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `BOT_TOKEN` | From @BotFather |
| `MONGO_URI` | MongoDB Atlas URI |
| `DB_CHANNEL` | File storage channel ID |
| `FORCE_SUB_CHANNEL` | Force-sub channel ID |
| `FORCE_SUB_INVITE` | Force-sub invite link |
| `ADMINS` | Comma-separated admin user IDs |
| `REQUEST_CHANNEL` | Channel to receive movie requests |
| `CHANNEL_URL` | Your public channel link |
| `SUPPORT_URL` | Your support group link |
| `AUTO_DELETE_SECONDS` | Delete timer (default: 300) |
| `MAX_RESULTS` | Max files per search (default: 10) |
| `RENDER_URL` | Your Render URL for self-ping |

---

## 🤖 User Commands

| Command | Description |
|---|---|
| `/start` | Welcome screen |
| `/request <movie>` | Request a missing movie |
| `/myrequests` | View your requests |
| `/ping` | Check bot status |
| `/help` | All commands |

## 🛠️ Admin Commands

| Command | Description |
|---|---|
| `/admin` | Open admin panel |
| `/ban <id> [reason]` | Ban a user |
| `/unban <id>` | Unban a user |
| `/stats` | Quick stats |

---

## 📜 License

MIT — free to use and modify.

---
<div align="center">Made with ❤️ — CinemaCityHub v3.0</div>
