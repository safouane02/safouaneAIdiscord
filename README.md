# Discord AI Bot 🤖

بوت ديسكورد مبني بـ Python يعتمد على **Groq AI** (Llama 3) مجاناً.

## الميزات

- 💬 محادثة طبيعية عبر نظام الـ Reply
- 🧠 ذاكرة محادثة per-user (آخر 10 رسائل)
- 🎭 شخصيات AI قابلة للتغيير (`!mode`)
- ⏳ Rate limiting (10 رسائل/دقيقة per-user)
- 📝 Logging كامل في `logs/bot.log`
- ⚠️ معالجة أخطاء شاملة

## التثبيت

```bash
git clone https://github.com/safouane02/discord-ai-bot
cd discord-ai-bot

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

## الإعداد

```env
DISCORD_TOKEN=your_discord_token
GROQ_API_KEY=your_groq_api_key
```

**Discord Token:** https://discord.com/developers/applications
→ New Application → Bot → Reset Token → فعّل **Message Content Intent**

**Groq API Key (مجاني):** https://console.groq.com

## التشغيل

```bash
python bot.py
```

## الأوامر

| الأمر | الوظيفة |
|-------|---------|
| `!ask <سؤال>` | سؤال مباشر بدون سياق |
| `!mode <اسم>` | تغيير شخصية الـ AI |
| `!clear` | مسح سجل المحادثة |
| `!ping` | فحص الاتصال |
| `!info` | معلومات البوت وشخصيتك الحالية |
| `!help` | قائمة الأوامر |

## الشخصيات المتاحة (`!mode`)

| الاسم | الوصف |
|-------|-------|
| `default` | مساعد ودود وعام |
| `sarcastic` | ساخر لكن مفيد |
| `teacher` | معلم صبور يشرح خطوة بخطوة |
| `developer` | مهندس برمجيات خبير |

## هيكل المشروع

```
discord-ai-bot/
├── bot.py
├── requirements.txt
├── .env.example
├── logs/
│   └── bot.log
└── src/
    ├── config.py
    ├── handlers/
    │   ├── commands.py
    │   └── reply_handler.py
    └── services/
        ├── groq_service.py
        ├── history.py
        ├── rate_limiter.py
        └── logger.py
```
