# Bizning Chat Bot 💬

Sevishgan juftliklar uchun maxsus chat va media kutubxonasi (kino, musiqa, rasm, video) taqdim etuvchi Telegram bot.

## Imkoniyatlar

- **💕 Sevishganlar uchun** — admin qo'shgan kino, musiqa, rasm va videolarni ko'rish
- **💬 Bizning chat** — username orqali juftlikka ulanish, so'rov yuborish/qabul qilish, va real vaqtda xabar almashish (matn, rasm, video, audio, ovozli xabar, stiker)
- **🟢/🔴 Online/Offline** — juftingizning oxirgi faolligi asosida hisoblangan holat
- **👨‍💼 Admin panel** — kontentni qo'shish, o'chirish, tahrirlash va ro'yxatini ko'rish

## Muhim texnik cheklov: "yozyapti..." holati

Telegram Bot API foydalanuvchi tomonidan yozilayotgan xabarni **botga bildirmaydi** — bu faqat oddiy foydalanuvchilar o'rtasidagi shaxsiy chatlarda ishlaydi, botlar buni ko'ra olmaydi (bu Telegram platformasining o'zi qo'ygan cheklov, dasturiy yechim bilan aylanib o'tib bo'lmaydi). Shu sababli haqiqiy vaqtli "✍️ yozyapti..." indikatorini soxta qilib ko'rsatmadik. Buning o'rniga **haqiqiy va ishonchli** bo'lgan online/offline holatini oxirgi faollik vaqti asosida to'liq amalga oshirdik.

## Texnologiyalar

- Python 3.11+
- aiogram 3.x
- PostgreSQL + SQLAlchemy 2.0 (async) + asyncpg

## Loyiha strukturasi

```
bizning-chat-bot/
├── main.py
├── config.py
├── database/
│   ├── models.py
│   ├── database.py
│   └── queries.py
├── handlers/
│   ├── start.py
│   ├── couple.py
│   ├── chat.py
│   ├── content.py
│   ├── admin.py
│   └── states.py
├── keyboards/
│   └── reply.py
├── middlewares/
│   ├── db.py
│   └── user.py
├── utils/
│   └── helpers.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── railway.toml
```

## Database jadvallari

`users`, `couples`, `pair_requests`, `messages`, `content`. Barcha jadvallar avtomatik yaratiladi.

## O'rnatish (lokal)

1. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env.example` dan nusxa oling va to'ldiring:
   ```bash
   cp .env.example .env
   ```

3. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## Railway'da deploy qilish

1. GitHub'ga loyihani joylang.
2. Railway'da yangi loyiha yarating va shu GitHub repo'ni ulang.
3. Loyihaga PostgreSQL xizmatini qo'shing.
4. Bot xizmatiga `BOT_TOKEN`, `DATABASE_URL`, `ADMIN_IDS` qo'shing.
5. Railway `Dockerfile` orqali botni build va deploy qiladi.

## Foydalanish

- `/start` — botni boshlash
- `/admin` — admin panel

### Juftlikka ulanish

1. "💬 Bizning chat" → "👤 Username orqali ulanish"
2. Juftingizning username'ini yuboring (masalan: @username)
3. So'rov yuboriladi — u qabul qilishi kerak
4. Qabul qilingandan keyin "💬 Bizning chat" orqali muloqot qiling

### Admin: kontent qo'shish

`/admin` → turini tanlang → "➕ Qo'shish" → faylni, nomini va tavsifini yuboring.
