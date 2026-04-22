# SF Discord Bot

A feature-rich Discord bot built with Python, focused on moderation, support workflows, and AI-assisted interactions.

## Features

- AI chat in DMs and ticket channels
- Moderation commands (ban, kick, timeout, warn, etc.)
- Ticket system with staff escalation and transcript export
- Leveling/XP system with role rewards
- Broadcast DM tools for server admins
- Premium-aware feature controls
- Optional FastAPI dashboard backend

## Tech Stack

- Python 3.10+
- `discord.py`
- `fastapi` + `uvicorn`
- `aiosqlite`
- `groq` API integration

## Project Structure

```text
.
├── bot.py
├── api.py
├── requirements.txt
├── .env.example
├── src/
│   ├── handlers/
│   └── services/
├── data/              # runtime-generated data (ignored by git)
└── logs/              # runtime logs (ignored by git)
```

## Quick Start

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
cp .env.example .env
```

5. Fill in the required values in `.env`, then run:

```bash
python bot.py
```

## Required Environment Variables

At minimum, set:

- `DISCORD_TOKEN`
- `GROQ_API_KEY`
- `OWNER_ID`
- `WHITELIST_PASSWORD`

If you use the API/dashboard, also set strong values for:

- `API_SECRET`
- `JWT_SECRET`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`

## Security and Privacy Notes

- Never commit `.env` or secret keys.
- Keep `API_SECRET` and `JWT_SECRET` random and private.
- Runtime logs and ticket data are intentionally excluded from git.
- Review Discord permissions before enabling moderation and broadcast commands.

## Deployment Notes

- The repository includes `.discloudignore` and `discloud.config` for Discloud deployment.
- You can deploy to other hosts as long as environment variables are configured correctly.

## Recommended First Commands

- `!ticketsetup` to initialize ticket channels and roles
- `!help` to view available commands

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Open a pull request

## License

Add a license file (`LICENSE`) before public distribution.
