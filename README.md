# 🖥️ py-webserver

A self-hosted personal web server running on a home machine, featuring a general-purpose website, a Minecraft server dashboard, and an integrated Discord bot - all secured behind nginx, HTTPS, and fail2ban.

## Stack

- **Backend:** Python, Flask, Gunicorn (gevent workers)
- **Reverse Proxy:** nginx (HTTPS via Let's Encrypt)
- **Auth & Security:** Session-based login, fail2ban rate limiting, server-side signed sessions
- **Discord Bot:** discord.py with slash commands
- **Dynamic DNS:** DuckDNS
- **Automation:** cron jobs

## Features

### 🌐 Web Server
- Session-based authentication with login-gated routes
- Role-based access (some routes restricted to specific users)
- Modular Flask routing across multiple route files
- Server-side sessions stored on disk with signed cookie IDs
- Auth event logging to `logs/auth.log`
- Secure cookies (HttpOnly, SameSite, HTTPS-only)
- nginx reverse proxy forwarding real client IPs via `ProxyFix`

### 🎮 Minecraft Dashboard
- Start/stop the server from the browser or Discord
- Live log streaming via Server-Sent Events (non-blocking via gevent)
- Player join/leave tracking in real time
- In-game command execution from the dashboard
- Server state persisted to `minecraft_state.json` across restarts
- Uptime alerts posted to Discord at 5h, 10h, 15h, 16h, 17h+ marks
- Achievement announcements posted to Discord
- Auto-backup every 15 minutes (rolling 5-backup window) with Discord webhook reporting

### 🤖 Discord Bot
- `/start` and `/stop` slash commands to control the Minecraft server
- Rich Presence (RPC) showing server status and live player count
- Communicates with the Flask app via a local WebSocket (port 8765)
- Bot API key authentication for internal bot→server requests

### 🔒 Security
- **fail2ban** monitors `auth.log` and bans IPs after repeated failed logins
- **nginx** enforces HTTPS and redirects all HTTP traffic
- **Let's Encrypt** SSL with auto-renewal support
- Old sessions purged every 10 minutes via cron
- Gunicorn runs locally only (`127.0.0.1`), never exposed directly

## Repo Structure (built for readability not 1:1 accuracy)

```
├── webserver/
│   ├── app.py                  # Main Flask app
│   ├── minecraft.py            # Minecraft dashboard Flask app (separate Gunicorn instance)
│   ├── minecraft_bot.py        # Discord bot + WebSocket server
│   ├── users.json              # Allowed users
│   ├── routes/
│   │   ├── cli.py
│   │   ├── fileManager.py
│   │   ├── login.py
│   │   ├── performance.py
│   │   └── public.py
│   └── templates/
│       ├── global/             # Shared header/footer
│       └── *.html
├── mcServers/
│   ├── autoBPs/autoBP.py       # Rolling backup manager
│   ├── minecraft_state.json    # Persistent server state
│   └── mcserver/
├── duckdns/duck.sh             # DuckDNS IP updater
├── configs/                    # nginx, fail2ban, systemd service configs
└── webServerUpdaters/          # Auto-update scripts
```

## Services

Two separate Gunicorn instances run as systemd services:

| Service | App | Port |
|---|---|---|
| `mike-server` | `app.py` | `5000` |
| `mike-minecraft` | `minecraft.py` | `5001` |

nginx routes `/minecraft` to port `5001` (with SSE support - buffering disabled) and everything else to port `5000`.

## Cron Jobs

| Schedule | Task |
|---|---|
| Every 2 min | Pull latest server updates |
| Every 5 min | DuckDNS domain refresh |
| Every 10 min | Purge expired sessions |
| Every 15 min | Auto-backup Minecraft world |

## Setup

> This is a personal self-hosted project. Configuration requires adjusting paths, credentials, and domain names throughout.

1. Clone the repo and set up a Python venv (`server-venv/init.sh`)
2. Copy configs from `configs/` to their respective system locations (nginx, fail2ban, systemd)
3. Create a `.env` file with:
```
FLASK_SECRET_KEY=
FLASK_SESSION_TYPE=filesystem
FLASK_SESSION_DIR=./sessions
DISC_BOT_TOKEN=
BOT_API_KEY=
TESTING=False
```
4. (opt.) Set up DuckDNS and insert your domain/token into `duck.sh`
5. Obtain SSL certs via Certbot: `sudo certbot --nginx -d yourdomain.duckdns.org`
6. Enable and start the systemd services
7. Start the Discord bot: `./launch_bot.sh`
