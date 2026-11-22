# MENING HUDUDIM 🇺🇿
> **Shior:** "Muammolar ko‘rinadi — yechimlar boshlanadi!"

O‘zbekiston fuqarolari va davlat tashkilotlari o‘rtasida ochiq muloqot va jamoatchilik nazoratini ta’minlovchi zamonaviy, to‘liq ishlaydigan milliy veb-platforma.

---

## 🌟 Asosiy imkoniyatlar

1. **Fuqarolar uchun:**
   - **Muammo yuborish:** Buzilgan yo‘llar, ichimlik suvi, ko‘cha chiroqlari, chiqindilar, kanalizatsiya va ekologik muammolar haqida xabar berish.
   - **Interaktiv xaritadan tanlash:** Leaflet.js orqali xaritada nuqtani belgilash yoki geolokatsiya orqali joylashuvni avtomatik aniqlash.
   - **Foto va video yuklash:** Real dalillarni serverda tekshirish (10MB rasm, 25MB video limitlari).
   - **Noyob murojaat raqami:** Har bir murojaatga `MH-2026-XXXXX` formatida noyob kod beriladi.
   - **Murojaatni kuzatish:** Ro‘yxatdan o‘tmagan holda ham raqam orqali holatni, qabul qilingan choralarni va tashkilotning rasmiy javobini ko‘rish.
   - **Shaxsiy kabinet:** Ro‘yxatdan o‘tish, profilni tahrirlash va yuborilgan barcha murojaatlar tarixini bir joyda kuzatish.

2. **O‘zbekiston bo‘yicha interaktiv xarita:**
   - OpenStreetMap va Leaflet.js asosida 14 ta viloyat/respublika xaritasi.
   - Holatiga ko‘ra rangli markerlar (Yangi, Jarayonda, Biriktirilgan, Hal etilgan, Rad etilgan).
   - Kategoriya, viloyat va status bo‘yicha filtrlar.
   - Marker bosilganda popup va to‘g‘ridan-to‘g‘ri murojaat sahifasiga o‘tish.

3. **Professional Admin Panel (Boshqaruv Portali):**
   - **Dashboard:** Jami murojaatlar, yangi, ko‘rib chiqilayotgan, hal etilgan va rad etilganlar soni.
   - **Diagrammalar (Chart.js):** Kategoriyalar bo‘yicha doughnut diagramma va hududlar kesimidagi ustunli statistika.
   - **Murojaatlarni boshqarish:** Qidiruv, multi-filtr, saralash va sahifalash (pagination).
   - **Murojaatni mas'ulga biriktirish:** Hududiy xodimlarni biriktirish va statusni o‘zgartirish (avtomatik `ReportHistory` yoziladi).
   - **Rasmiy javob yozish:** Tashkilot nomidan saytda ko‘rinadigan rasmiy javob va tushuntirish kiritish.
   - **CSV Eksport:** Murojaatlar ro‘yxatini Excel/CSV formatida to‘liq yuklab olish.
   - **Rollar va ruxsatlar:** Super Admin, Administrator, Hududiy mas'ul xodim (faqat o‘z hududini ko‘radi), Fuqaro.

---

## 🛠 Texnologiyalar

- **Backend:** Python 3.14+, Django 6+
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5.3, Font Awesome 6.5
- **Xaritalar:** Leaflet.js, OpenStreetMap
- **Diagrammalar:** Chart.js 4.4
- **Database:** SQLite 3 (Production uchun PostgreSQL ga to‘liq mos)
- **Arxitektura:** Django Apps modular pattern (`accounts`, `locations`, `reports`, `dashboard`)

---

## 🚀 Loyihani ishga tushirish

### 1. Papkaga o‘tish va virtual muhitni faollashtirish
```bash
cd /home/abdulloh/mening_hududim
source venv/bin/activate
```

### 2. Muhit sozlamalari (`.env`)
`.env.example` asosida `.env` fayli yaratilgan (yoki yangilangan). Undagi asosiy qiymatlar:

| O‘zgaruvchi | Tavsif |
|---|---|
| `SECRET_KEY` | Django maxfiy kaliti (production uchun yangi tasodifiy kalit qo‘ying) |
| `DEBUG` | Mahalliy ishlab chiqishda `True`, productionda `False` |
| `ALLOWED_HOSTS` | Ruxsat etilgan hostlar. Boshqa qurilmadan (LAN IP orqali) kirish uchun IP ni ro‘yxatga qo‘shing |
| `SITE_URL` | Telegram xabarlaridagi havolalar uchun saytning to‘liq manzili |
| `TELEGRAM_BOT_TOKEN` | @BotFather dan olingan bot tokeni |
| `TELEGRAM_ADMIN_ID` | Admin xabarlari yuboriladigan chat ID |

> Productionga chiqarishda `DEBUG=False` qiling, `SECRET_KEY` ni almashtiring va `ALLOWED_HOSTS` ga faqat o‘z domeningizni yozing.

### 3. Kutubxonalarni o‘rnatish
```bash
pip install -r requirements.txt
```

### 4. Migratsiyalarni qo‘llash
```bash
python manage.py migrate
python manage.py check
```

### 5. Boshlang‘ich ma’lumotlarni to‘ldirish (faqat O‘zbekiston viloyatlari, tumanlari va kategoriyalar)
```bash
python seed_data.py
```

### 6. Serverni ishga tushirish
```bash
python manage.py runserver 8000
```
Yoki tayyor skript orqali:
```bash
./run.sh
```

Brauzerda oching: **http://127.0.0.1:8000**

### 7. Telegram botni ishga tushirish (ixtiyoriy)
```bash
./run_bot.sh
```
Bot `.env` dagi `TELEGRAM_BOT_TOKEN` va `SITE_URL` qiymatlaridan foydalanadi. Tokensiz ishga tushirish rad etiladi.

### 8. Sinovlar
```bash
python manage.py test
```

---

## 🔑 Boshqaruv hisoblari

Demo/sinov foydalanuvchilari va test murojaatlari olib tashlangan. Tizim faqat haqiqiy ma’lumotlar bilan ishlaydi.

| Rol | Login | Parol | Huquqlar |
|---|---|---|---|
| **Super Admin** | `Abu` | bir marta ko‘rsatiladi | Barcha vakolatlar, barcha viloyatlar, Django Admin |
| **Bosh Admin** | `bosh_admin` | bir marta ko‘rsatiladi | Abu bilan bir xil huquq, hammasini ko‘radi |
| **14 viloyat administratori** | `admin_ts`, `admin_tv`, … | bir marta ko‘rsatiladi | Faqat o‘z viloyati; Django Admin yo‘q |

Parollar hech qayerda saqlanmaydi: `python seed_data.py` dastlabki parolni bir marta chop etadi. Ammo siz tanlagan parolni `SEED_ABU_PASSWORD` muhit o‘zgaruvchisi bilan ham berishingiz mumkin. `admin`, `toshkent_staff`, `fuqaro`, `samarqand_staff`, `sobir_usta`, `adminaa` — barchasi o‘chirilgan.

Super Adminlar **Xodimlar → Viloyat adminlari** sahifasidan viloyat adminlarini yaratadi. **Viloyat admini** esa o‘z panelidan **Xodimlar → Yangi xodim qo‘shish** orqali usta/hududiy xodim qo‘shadi va ularni darhol tasdiqlaydi (boshqa viloyatni tanlay olmaydi). Ishchi qo‘shishda **telefon majburiy**, **email ixtiyoriy**. Yangi parollar bir marta ko‘rsatiladi; kirishdan keyin parolni **Sozlamalar** sahifasida ixtiyoriy o‘zgartirish mumkin. Fuqarolar esa ro‘yxatdan o‘tish sahifasidan o‘z hisobini ochadi (ariza topshirishda telefon majburiy).

**Xavfsizlik choralari:** parol kamida 12 belgi va keng tarqalgan/raqamli parollar rad etiladi; login va murojaat qidiruviga cheklov qo‘yilgan; CSV eksportida formula inyeksiyasi oldi olingan; grafik ma’lumotlari `json_script` orqali XSS’siz uzatiladi; xodimlar Django admin sahifasiga kira olmaydi; viloyat admini boshqa viloyat murojaatini ko‘ra va tahrirlay olmaydi.

> Production muhitda Abuning parolini darhol almashtiring: `python manage.py changepassword Abu`. `.env` fayli va Telegram tokeni hech qachon Git’ga qo‘shilmaydi — ularni serverda alohida yarating.

---

## 🗺️ O‘zbekiston xaritasi va interfeys

- **Dizayn:** oq zamin va och ko‘k aksentlar, yengil ko‘k chegaralar, yumshoq soyalar — barcha sahifalarda yagona. Yuqori navbar (logo, qidiruv, profil) va pastki qism (mobil panel + footer) ham shu standart uslubda.
- Xarita **butun O‘zbekiston chegarasiga moslashtirilgan**, ustida 14 ta viloyat/respublikaning haqiqiy chegaralari chizilgan (GeoJSON: [akbartus/GeoJSON-Uzbekistan](https://github.com/akbartus/GeoJSON-Uzbekistan)). Asos xarita yengil (CartoDB Positron) bo‘lib, mamlakat shakli aniq ko‘rinadi.
- Viloyat ustiga bosilsa filtr tanlanadi va xarita shu hududga yaqinlashadi; yon panelda barcha 14 hudud va murojaatlar soni ko‘rsatiladi. Kichik holat paneli yopiq holda ochiladi va qayta ochish tugmasi bilan ko‘rsatiladi.
- **Chap navigatsiya menyusi** yuqori paneldagi `«` tugmasi yoki menyu sarlavhasidagi tugma bilan ochilib-yopiladi. Yopilganda chap tomonda `☰` tugmasi paydo bo‘ladi. Holat brauzerda saqlanadi.
- **Barcha ko‘rinish boshqaruvlari bitta joyda:** pastki o‘ng burchakdagi `☰` tugmasi bitta panelni ochadi. Unda:
  - **Bo‘limlar** — barchasini bir vaqtda ochish/yig‘ish;
  - **O‘lcham** — `Kichik / O‘rta / Katta / Avto` (ekranga moslashadi, tanlov saqlanadi);
  - **Yon panel** — chap navigatsiyani yopish/ochish.
- Har bir sahifadagi bo‘limlar sarlavhasiga bosib ham ochilib-yig‘iladi. Matn, ikonkalar, kartalar va xarita balandligi o‘lcham bilan birgalikda o‘zgaradi.

---

## 📁 Papkalar Strukturasi

```
mening_hududim/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── seed_data.py
├── run.sh
├── config/                  # Django asosiy loyiha sozlamalari
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # Foydalanuvchilar, rollar, autentifikatsiya
│   ├── models.py            # Custom User modeli (citizen, regional_staff, admin, superadmin)
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── locations/               # O‘zbekiston viloyatlari va tumanlari
│   ├── models.py            # Region, District
│   ├── views.py             # Dinamik tumanlar APIsi
│   └── urls.py
├── reports/                 # Murojaatlar tizimi
│   ├── models.py            # Category, Report, ReportHistory, AdminReply
│   ├── forms.py             # Validatsiyali murojaat formasi
│   ├── views.py             # Bosh sahifa, xarita, ro‘yxat, detal, qidiruv
│   ├── urls.py
│   └── context_processors.py
├── dashboard/               # Professional Admin / Xodimlar Portali
│   ├── views.py             # Analytics, Chart.js ma'lumotlari, CSV eksport
│   └── urls.py
├── templates/               # Zamonaviy HTML shablonlar
│   ├── base.html
│   ├── navbar.html
│   ├── footer.html
│   ├── home.html
│   ├── about.html
│   ├── track.html
│   ├── 404.html, 500.html
│   ├── accounts/
│   ├── reports/
│   └── dashboard/
├── static/                  # CSS, JS, Ikonlar
│   ├── css/style.css        # Premium White + Blue dizayn tizimi
│   └── js/
│       ├── main.js          # Dinamik tuman yuklash, nusxalash, preview
│       └── map.js           # Leaflet xaritasi, markerlar, popup
└── media/                   # Yuklangan fotosuratlar va videolar
```

---

## 🔒 Xavfsizlik

- Barcha so‘rovlar CSRF token bilan himoyalangan; chiqish (logout) faqat POST orqali amalga oshiriladi.
- Parollar Django validation qoidalari bilan tekshirilib, PBKDF2 hash algoritmi bilan saqlanadi.
- XSS va SQL Injection himoyasi (Django ORM, template auto-escaping, xarita popup va Telegram xabarlarida HTML escape).
- Login/register `next` parametri faqat mahalliy manzillarga ruxsat beradi (open redirect yo‘q).
- Yuklanadigan fayllar turi va hajmi server tomonida qat'iy tekshiriladi (10 MB rasm, 25 MB video).
- Rolga asoslangan kirish nazorati (RBAC): fuqarolar boshqaruv portaliga kira olmaydi, hududiy xodimlar faqat o‘z viloyatini ko‘radi.
- Murojaatga faqat mavjud mas'ul xodim biriktirilishi mumkin; oxirgi faol superadmin o‘chirilmaydi.
