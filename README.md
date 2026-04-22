<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=timeGradient&height=250&section=header&text=SF%20Discord%20Bot&fontSize=90" alt="Header Image" />
  
  # 🤖 SF Discord Bot
  
  **An Advanced, AI-Powered Discord Moderation & Management Assistant**
  
  [![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![Discord.py](https://img.shields.io/badge/Discord.py-2.0+-blue.svg?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](#-license)
  [![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
</div>

---

## 📖 Table of Contents
- [About The Project](#-about-the-project)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#-configuration)
- [Security & Best Practices](#-security--best-practices)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 About The Project

**SF Discord Bot** is a production-grade Discord bot designed to automate server moderation, provide AI-powered assistance, and streamline community management. Whether you're running a small community or a massive server, SF Bot provides the necessary tools to keep your server safe, active, and engaging.

Unlike traditional bots, SF Bot integrates an **Advanced AI Assistant** (powered by Groq) to handle support queries dynamically and includes a built-in **FastAPI backend** to seamlessly connect with external dashboards (like Next.js).

---

## ✨ Key Features

🛡️ **Advanced Moderation Suite**
- Comprehensive commands: Ban, Kick, Timeout, Warn, Mute, Clear, and Softban.
- Smart Automod capabilities to prevent spam and toxic behavior.
- Advanced logging for all administrative actions.

🎫 **Automated Ticket System**
- Allow users to easily open support tickets.
- Dedicated staff workflows (claim, close).
- Generate and download HTML transcripts for record-keeping.

🧠 **AI-Powered Assistance**
- Smart conversational AI built using the Groq API.
- Multiple unique personalities (Default, Sarcastic, Teacher, Developer, Roast).
- Natural language query resolution for community members.

📈 **Leveling & Engagement**
- Dynamic XP and leveling system.
- Leaderboards to foster community activity.
- Configurable XP rates and automated role rewards.

👑 **Premium Management & Subscriptions**
- Built-in tier system to gate exclusive features.
- Track AI token usage per server to manage API costs.

🌐 **FastAPI Web & Dashboard Integration**
- Built-in REST API to power Next.js or React dashboards.
- Secure JWT-based Discord OAuth authentication.

---

## 💻 Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Core** | `Python 3.10+` | Main programming language |
| **Discord Library** | `discord.py` | Official Discord API wrapper |
| **Backend API** | `FastAPI` & `Uvicorn` | High-performance async web framework |
| **Database** | `aiosqlite` | Asynchronous SQLite for robust local storage |
| **AI Integration**| `Groq API` | Ultra-fast LLM inference API |

---

## 🏗 Architecture

```text
📦 sf-discord-bot
 ┣ 📂 src
 ┃ ┣ 📂 handlers       # Discord command cogs & event listeners
 ┃ ┣ 📂 services       # Business logic (DB, AI, Tickets, Premium)
 ┃ ┗ 📜 config.py      # Core runtime configurations
 ┣ 📂 data             # Local SQLite databases (Auto-generated)
 ┣ 📂 logs             # App and error logs (Auto-generated)
 ┣ 📂 nextjs-integration # Setup guides for web dashboards
 ┣ 📜 bot.py           # Main Bot entry point
 ┣ 📜 api.py           # FastAPI server entry point
 ┣ 📜 requirements.txt # Python dependencies
 ┗ 📜 .env.example     # Environment variables template
```

---

## 🚀 Getting Started

Follow these instructions to set up your own instance of the SF Discord Bot.

### Prerequisites

- **Python 3.10 or higher** installed on your machine.
- A **Discord Bot Token** (Create an application at the [Discord Developer Portal](https://discord.com/developers/applications)).
- A **Groq API Key** for AI features (Get it from [Groq Console](https://console.groq.com/)).

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/safouane02/safouaneAIdiscord.git
   cd safouaneAIdiscord
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy the example config file:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and fill in your credentials. (See [Configuration](#-configuration))

5. **Run the Bot**
   ```bash
   python bot.py
   ```
   *The FastAPI server will automatically start on port 8000 if `ENABLE_API=true` in your `.env`.*

---

## ⚙️ Configuration

Your `.env` file should contain the following variables:

| Variable | Description | Required |
|----------|-------------|:---:|
| `DISCORD_TOKEN` | Your Discord Bot Token | ✅ |
| `OWNER_ID` | Your Discord User ID for administrative overrides | ✅ |
| `BOT_PREFIX` | Default command prefix (e.g., `!`) | ✅ |
| `GROQ_API_KEY` | Key for AI features | ✅ |
| `WHITELIST_PASSWORD` | Password for accessing the bot in DMs | ✅ |
| `ENABLE_API` | Set to `true` to enable FastAPI | ❌ |
| `API_PORT` | Port for the FastAPI server (Default: `8000`) | ❌ |
| `API_SECRET` | Secret for internal API authentication | ❌ |
| `JWT_SECRET` | Secret for encoding Dashboard JWT tokens | ❌ |
| `DISCORD_CLIENT_ID`| For Dashboard OAuth integration | ❌ |
| `DISCORD_CLIENT_SECRET`| For Dashboard OAuth integration | ❌ |

---

## 🔒 Security & Best Practices

- **Never share your `.env` file:** It is included in `.gitignore` to prevent accidental uploads.
- **Bot Intents:** Ensure you have enabled **Message Content Intent**, **Server Members Intent**, and **Presence Intent** in the Discord Developer Portal.
- **Deployment:** For production, it is highly recommended to use a process manager like `pm2`, `systemd`, or Docker to keep the bot running 24/7.
- **Permissions:** Only grant the bot the permissions it strictly needs (Admin is recommended only for initial setup or private servers).

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
<div align="center">
  <i>Developed with ❤️ by <a href="https://github.com/safouane02">Safouane Baadoud</a></i>
</div>
