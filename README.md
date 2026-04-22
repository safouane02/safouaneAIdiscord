# SF Discord Bot

Production-ready Discord bot focused on moderation, support automation, and AI-powered assistance.  
Built for communities that need fast tooling, clean workflows, and scalable server operations.

## Why This Project

Managing active Discord communities requires more than basic commands. This bot combines:

- strong moderation controls,
- ticket-based support operations,
- leveling and community engagement,
- optional API/dashboard integration,
- AI features for faster staff and user interactions.

## Core Features

- **Moderation Suite**: ban, kick, timeout, warn, softban, lock/unlock, clear, snipe, and more.
- **Ticket System**: open/close workflows, staff access, and transcript exports.
- **AI Assistant**: AI responses in DMs and support contexts.
- **Leveling & Rewards**: XP progression, leaderboard support, and role rewards.
- **Broadcast Tools**: admin-focused messaging and utility actions.
- **Premium Controls**: feature gating and usage-aware tiers.
- **Web/API Layer**: FastAPI endpoints for dashboard and integrations.

## Tech Stack

- **Language**: Python 3.10+
- **Discord Framework**: `discord.py`
- **API Backend**: `fastapi`, `uvicorn`
- **Database**: `aiosqlite`
- **AI Integration**: Groq API

## Architecture

```text
.
├── bot.py                      # Discord bot entry point
├── api.py                      # FastAPI backend (optional dashboard/api)
├── requirements.txt
├── .env.example
├── src/
│   ├── handlers/               # Discord commands/events/cogs
│   ├── services/               # business logic, db, ai, moderation, tickets
│   └── config.py               # runtime settings
├── data/                       # runtime-generated data (git ignored)
├── logs/                       # runtime logs (git ignored)
├── discloud.config             # Discloud deployment config
└── .discloudignore
```

## Quick Start

### 1) Clone

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2) Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment

Create `.env` from template:

```bash
copy .env.example .env
```

Then fill required values.

### 5) Run the bot

```bash
python bot.py
```

Optional API service:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Environment Variables

### Required (Bot)

- `DISCORD_TOKEN`
- `GROQ_API_KEY`
- `OWNER_ID`
- `WHITELIST_PASSWORD`

### Required (API/Dashboard)

- `API_SECRET`
- `JWT_SECRET`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`

## Security Best Practices

- Never commit `.env`, tokens, or private credentials.
- Rotate keys immediately if any secret is exposed.
- Keep `API_SECRET` and `JWT_SECRET` long and random.
- Do not commit runtime data (`data/`) or logs (`logs/`) to public repos.
- Use least-privilege bot permissions in Discord servers.

## Deployment

- Ready for Discloud with included `discloud.config` and `.discloudignore`.
- Can be deployed on any Linux/Windows host with Python and environment variables configured.
- For production, use a process manager (e.g., PM2, systemd, supervisor) and restart policies.

## Recommended First Commands

- `!help`
- `!ticketsetup`
- moderation commands based on your server policy

## Roadmap

- Better observability and metrics
- Extended dashboard controls
- More granular permission and role policies
- Additional language/localization support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit clear, scoped changes
4. Open a pull request with testing notes

## License

Add a `LICENSE` file before public distribution (MIT recommended for open-source usage).
