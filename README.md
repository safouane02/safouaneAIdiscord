# SF Discord Bot 🤖

بوت ديسكورد متكامل مبني بـ Python — يدعم الـ AI، المودريشن، نظام اللفلات، التكتات، وأكثر.

---

## المميزات

| الميزة | الوصف |
|--------|-------|
| 🤖 AI Chat | محادثة ذكية تعتمد على الرد على رسائل البوت |
| 🧠 Smart Model Selection | يختار الموديل تلقائياً حسب صعوبة السؤال |
| ⚡ Token Optimization | Cache + ضغط Prompt + توزيع API Keys |
| 🔨 Moderation | ban, kick, mute, warn, timeout وأكثر |
| ⭐ Level System | XP، لفلات، رتب تلقائية عند الوصول لفل |
| 🎫 Ticket System | تكتات AI مع escalation تلقائي للستاف |
| 📨 Broadcast | إرسال DM جماعي لكل الأعضاء أو رتبة معينة |
| 🔐 DM Whitelist | تحكم في من يقدر يكلم البوت في البريفي |
| 📊 Multi-Server | قاعدة بيانات مستقلة لكل سيرفر |

---

## التثبيت

```bash
git clone https://github.com/safouane02/discord-ai-bot
cd discord-ai-bot

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

---

## الإعداد

عدّل ملف `.env`:

```env
DISCORD_TOKEN=your_discord_token
GROQ_API_KEY=your_groq_api_key
OWNER_ID=your_discord_user_id
WHITELIST_PASSWORD=your_secret_password

SUPPORT_ROLE=Support
TICKET_CATEGORY=Tickets

# مفاتيح إضافية لتوزيع الحمل (اختياري)
# GROQ_API_KEY_2=second_key
# GROQ_API_KEY_3=third_key
```

**Discord Token:**
1. اذهب إلى https://discord.com/developers/applications
2. New Application → Bot → Reset Token
3. فعّل **Message Content Intent** و **Server Members Intent**

**Groq API Key (مجاني):** https://console.groq.com

**OWNER_ID:** في Discord فعّل Developer Mode → كليك يمين على اسمك → Copy User ID

---

## التشغيل

```bash
python bot.py
```

---

## إعداد السيرفر (مرة واحدة)

```
!ticketsetup
```

يُنشئ تلقائياً: رتبة Support، كاتيجوري Tickets، قناة open-ticket بزر.

---

## الأوامر

### 🤖 AI
| الأمر | الوصف |
|-------|-------|
| `!ask <سؤال>` | سؤال مباشر |
| `!mode <n>` | تغيير الشخصية: `default` `sarcastic` `teacher` `developer` |
| `!clear_chat` | مسح سجل المحادثة |
| رد على رسالة البوت | محادثة مستمرة |

### 🔨 Moderation
| الأمر | الوصف |
|-------|-------|
| `!ban @user [reason]` | حظر دائم |
| `!unban <id>` | رفع الحظر |
| `!kick @user [reason]` | طرد مؤقت |
| `!softban @user` | حظر + حذف الرسائل + رفع الحظر |
| `!massban @u1 @u2` | حظر جماعي |
| `!timeout @user <مدة>` | تقييد مؤقت — `10m` `1h` `1d` |
| `!untimeout @user` | رفع التقييد |
| `!mute / !unmute @user` | كتم / رفع الكتم |
| `!warn @user [reason]` | تحذير |
| `!warnings @user` | عرض التحذيرات |
| `!history @user` | سجل المودريشن |

### 🛠️ Management
| الأمر | الوصف |
|-------|-------|
| `!clear <عدد>` | حذف رسائل |
| `!nuke` | إعادة إنشاء القناة |
| `!lock / !unlock` | قفل / فتح القناة |
| `!nick @user <اسم>` | تغيير الكنية |
| `!move @user #voice` | نقل لقناة صوتية |
| `!disconnect @user` | فصل من الصوت |
| `!role_add / !role_remove @user @role` | إضافة / حذف رتبة |
| `!announce #channel <رسالة>` | إعلان رسمي |
| `!say <رسالة>` | إرسال رسالة باسم البوت |
| `!snipe / !editsnipe` | آخر رسالة محذوفة / معدلة |
| `!steal_emoji <emoji>` | نسخ إيموجي من سيرفر آخر |
| `!invite` | رابط دعوة |

### ⭐ Levels
| الأمر | الوصف |
|-------|-------|
| `!rank [@user]` | عرض المستوى والـ XP |
| `!leaderboard` | أعلى 10 أعضاء |
| `!setlevelrole <level> @role` | رتبة عند الوصول لفل |
| `!removelevelrole <level>` | حذف رتبة فل |
| `!levelroles` | عرض كل رتب الفلات |
| `!levelsettings` | عرض إعدادات الـ XP |
| `!setlevelupchannel [#ch]` | قناة إعلانات الليفل أب |
| `!setlevelupmsg <رسالة>` | رسالة مخصصة — `{user}` `{level}` `{old_level}` |
| `!setxpboost <n>` | مضاعف XP — مثال: `2.0` |
| `!setxp @user <amount>` | تحديد XP يدوياً |
| `!resetxp @user` | مسح XP العضو |

### 🎫 Tickets
| الأمر | الوصف |
|-------|-------|
| `!ticketsetup` | إعداد نظام التكتات |
| `!ticketpanel` | تعديل رسالة البانيل |
| `!ticketmessage` | تعديل رسالة الترحيب في التكت |
| `!ticket` | فتح تكت جديد |
| `!close` | إغلاق التكت |
| `!claim` | استلام التكت (ستاف) |
| `!tadd @user` | إضافة شخص للتكت |
| `!transcript` | تحميل سجل المحادثة |
| `!ticketstats` | إحصائيات التكتات |

### ℹ️ Info
| الأمر | الوصف |
|-------|-------|
| `!serverinfo` | معلومات السيرفر |
| `!userinfo [@user]` | معلومات عضو |
| `!avatar [@user]` | صورة البروفايل |
| `!banner [@user]` | البانر |
| `!membercount` | عدد الأعضاء |
| `!channelinfo` | معلومات القناة |

### 📨 Broadcast
| الأمر | الوصف |
|-------|-------|
| `!dm all <رسالة>` | DM لكل الأعضاء |
| `!dm humans <رسالة>` | DM للبشر فقط |
| `!dm @role <رسالة>` | DM لرتبة معينة |

### 🔐 Admin (Owner فقط)
| الأمر | الوصف |
|-------|-------|
| `!add @user` | إضافة لـ DM whitelist |
| `!remove @user` | إزالة من الـ whitelist |
| `!whitelist` | عرض القائمة |
| `!info` | معلومات البوت |
| `!ping` | فحص الاتصال |

### 🤖 AI Moderation
اذكر البوت مع العضو بكلام طبيعي:
```
@Bot اطرد @ahmed لأنه يسبام
@Bot timeout @user لمدة ساعة بسبب الإزعاج
```
البوت يفهم القصد، يطلب تأكيداً، ثم ينفذ.

---

## نظام الموديلات

البوت يختار الموديل تلقائياً حسب صعوبة السؤال:

| الحالة | الموديل |
|--------|---------|
| سؤال قصير بسيط | Llama 4 Scout — أسرع |
| سؤال متوسط | GPT OSS 20B |
| سؤال عادي | Llama 3.3 70B |
| سؤال معقد / تحليل | Kimi K2 |
| كود أو رسالة طويلة | GPT OSS 120B |

---

## توفير التوكنز

- **Cache** — الأسئلة المتكررة تُجاب من الـ cache (6 ساعات)
- **Smart Prompt** — يرسل فقط الأوامر المتعلقة بالسؤال
- **History Compression** — آخر 4 رسائل فقط بدل 10
- **Key Rotation** — توزيع الطلبات على أكثر من API Key

---

## هيكل المشروع

```
discord-ai-bot/
├── bot.py
├── requirements.txt
├── .env
├── data/
│   ├── bot.db
│   ├── whitelist.json
│   ├── mod_logs.json
│   ├── tickets.json
│   └── ticket_config.json
├── logs/
│   └── bot.log
└── src/
    ├── config.py
    ├── handlers/
    │   ├── commands.py
    │   ├── mod_commands.py
    │   ├── admin_commands.py
    │   ├── reply_handler.py
    │   ├── dm_handler.py
    │   ├── ticket_commands.py
    │   ├── level_commands.py
    │   └── broadcast.py
    └── services/
        ├── groq_service.py
        ├── history.py
        ├── rate_limiter.py
        ├── logger.py
        ├── whitelist.py
        ├── moderation.py
        ├── mod_logger.py
        ├── snipe_store.py
        ├── ticket_store.py
        ├── ticket_ai.py
        ├── ticket_config.py
        ├── level_service.py
        ├── database.py
        ├── cache.py
        ├── key_pool.py
        ├── prompt_builder.py
        └── context_builder.py
```

---

## Developer

**Safouane Baadoud (صفوان باعود)**
- GitHub: [safouane02](https://github.com/safouane02)
- Location: Algeria
- Specialization: Full-Stack Developer & Automation Engineer