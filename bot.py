import functools
import html
import os
import re
import sys

import django

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import telebot
from telebot import types
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from reports.models import Category, Report, ReportHistory
from locations.models import Region, District

BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
ADMIN_ID = getattr(settings, 'TELEGRAM_ADMIN_ID', 0)
SITE_URL = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
PHONE_RE = re.compile(r'^\+?[0-9][0-9\s()\-]{6,24}$')

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')

# In-memory user states for multi-step report creation
user_states = {}


# ---------- Helpers ----------

def esc(value):
    """Escape user-provided text for Telegram parse_mode=HTML."""
    return html.escape(str(value if value is not None else ''), quote=False)


def local_dt(value):
    try:
        return timezone.localtime(value).strftime('%d.%m.%Y %H:%M')
    except (TypeError, ValueError):
        return str(value)


def chat_id_of(obj):
    chat = getattr(obj, 'chat', None)
    if chat is not None:
        return chat.id
    message = getattr(obj, 'message', None)
    if message is not None and getattr(message, 'chat', None) is not None:
        return message.chat.id
    return None


def safe_handler(func):
    """Never let one bad message break the polling loop or leave stale state."""
    @functools.wraps(func)
    def wrapper(update, *args, **kwargs):
        try:
            return func(update, *args, **kwargs)
        except Exception as exc:
            print(f"Bot handler error in {func.__name__}: {exc}")
            chat_id = chat_id_of(update)
            if chat_id is not None:
                try:
                    bot.send_message(
                        chat_id,
                        "Kechirasiz, kutilmagan xatolik yuz berdi. "
                        "Qaytadan urinib ko'ring yoki /start buyrug'ini bosing.",
                        reply_markup=get_main_keyboard()
                    )
                except Exception:
                    pass
            return None
    return wrapper


def parse_id(data, prefix):
    try:
        return int(str(data).split('_', 1)[1])
    except (IndexError, TypeError, ValueError):
        return None


def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_report = types.KeyboardButton("📢 Muammo haqida xabar berish")
    btn_track = types.KeyboardButton("🔍 Murojaatni tekshirish")
    btn_stats = types.KeyboardButton("📊 Statistika")
    btn_web = types.KeyboardButton("🌐 Veb-saytga o'tish")
    btn_about = types.KeyboardButton("ℹ️ Loyiha haqida")
    markup.add(btn_report)
    markup.add(btn_track, btn_stats)
    markup.add(btn_web, btn_about)
    return markup


# ---------- Commands ----------

@bot.message_handler(commands=['start', 'help'])
@safe_handler
def send_welcome(message):
    first_name = esc(getattr(message.from_user, 'first_name', 'fuqaro'))
    welcome_text = (
        f"Assalomu alaykum, <b>{first_name}</b>! 🇺🇿\n\n"
        f"<b>MENING HUDUDIM</b> rasmiy botiga xush kelibsiz!\n"
        f"<i>«Muammolar ko‘rinadi — yechimlar boshlanadi!»</i>\n\n"
        f"Ushbu bot orqali mahallangizdagi buzilgan yo‘llar, ichimlik suvi, ko‘cha chiroqlari, "
        f"chiqindilar va boshqa kommunal muammolar haqida to‘g‘ridan-to‘g‘ri fotosurat bilan xabar berishingiz mumkin.\n\n"
        f"Quyidagi menyudan kerakli bo‘limni tanlang:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())


@bot.message_handler(commands=['cancel'])
@safe_handler
def cancel_submission(message):
    user_states.pop(message.chat.id, None)
    bot.send_message(
        message.chat.id,
        "Joriy amal bekor qilindi.",
        reply_markup=get_main_keyboard()
    )


@bot.message_handler(commands=['admin'])
@safe_handler
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Kechirasiz, ushbu buyruq faqat boshqaruvchi (admin) uchun mo'ljallangan.")
        return

    total = Report.objects.count()
    new_cnt = Report.objects.filter(status=Report.STATUS_NEW).count()
    in_prog = Report.objects.filter(status=Report.STATUS_IN_PROGRESS).count()
    resolved = Report.objects.filter(status=Report.STATUS_RESOLVED).count()

    admin_msg = (
        f"🔐 <b>BOSHQARUV PANELI (ADMIN)</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• Jami murojaatlar: <b>{total}</b> ta\n"
        f"• 🔵 Yangi: <b>{new_cnt}</b> ta\n"
        f"• 🟡 Ko'rib chiqilmoqda: <b>{in_prog}</b> ta\n"
        f"• 🟢 Hal qilingan: <b>{resolved}</b> ta\n\n"
        f"🌐 <b>Sayt Boshqaruv Portali:</b>\n"
        f"{esc(SITE_URL)}/portal/\n\n"
        f"Oxirgi murojaatlarni ko'rish uchun: /recent"
    )
    bot.send_message(message.chat.id, admin_msg)


@bot.message_handler(commands=['recent'])
@safe_handler
def admin_recent(message):
    if message.from_user.id != ADMIN_ID:
        return

    reports = Report.objects.select_related('region').order_by('-created_at')[:5]
    if not reports:
        bot.send_message(message.chat.id, "Murojaatlar mavjud emas.")
        return

    text = "📋 <b>Oxirgi 5 ta murojaat:</b>\n\n"
    for r in reports:
        text += (
            f"• <code>{esc(r.tracking_code)}</code> — {esc(r.title[:35])}\n"
            f"  📍 {esc(r.region.name)} | Holat: {esc(r.get_status_display())}\n\n"
        )
    bot.send_message(message.chat.id, text)


# ---------- 1. Murojaat yuborish ssenariysi ----------

@bot.message_handler(func=lambda msg: msg.text == "📢 Muammo haqida xabar berish")
@safe_handler
def start_report_submission(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'category'}

    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat in Category.objects.all().order_by('order'):
        markup.add(types.InlineKeyboardButton(cat.name, callback_data=f"cat_{cat.id}"))

    bot.send_message(
        chat_id,
        "<b>1-qadam.</b> Muammo qaysi sohaga tegishli ekanligini tanlang:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
@safe_handler
def handle_category_chosen(call):
    chat_id = chat_id_of(call)
    state = user_states.get(chat_id)
    if not state or state.get('step') != 'category':
        bot.answer_callback_query(call.id, text="Avval murojaat yuborishni boshlang.")
        return

    cat = Category.objects.filter(pk=parse_id(call.data, 'cat_')).first()
    if not cat:
        bot.answer_callback_query(call.id, text="Kategoriya topilmadi.")
        return

    state['category_id'] = cat.pk
    state['step'] = 'region'
    bot.answer_callback_query(call.id, text=f"{cat.name} tanlandi")

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(reg.name, callback_data=f"reg_{reg.id}")
        for reg in Region.objects.all().order_by('order')
    ]
    if buttons:
        markup.add(*buttons)

    bot.edit_message_text(
        f"✅ Kategoriya: <b>{esc(cat.name)}</b>\n\n<b>2-qadam.</b> Muammo qaysi viloyat / hududda joylashgan?",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('reg_'))
@safe_handler
def handle_region_chosen(call):
    chat_id = chat_id_of(call)
    state = user_states.get(chat_id)
    if not state or state.get('step') != 'region':
        bot.answer_callback_query(call.id, text="Avval kategoriyani tanlang.")
        return

    reg = Region.objects.filter(pk=parse_id(call.data, 'reg_')).first()
    if not reg:
        bot.answer_callback_query(call.id, text="Hudud topilmadi.")
        return

    state['region_id'] = reg.pk
    state['step'] = 'district'
    bot.answer_callback_query(call.id, text=f"{reg.name} tanlandi")

    markup = types.InlineKeyboardMarkup(row_width=2)
    districts = District.objects.filter(region_id=reg.pk).order_by('name')[:30]
    buttons = [
        types.InlineKeyboardButton(dist.name, callback_data=f"dist_{dist.id}")
        for dist in districts
    ]
    if buttons:
        markup.add(*buttons)

    bot.edit_message_text(
        f"✅ Hudud: <b>{esc(reg.name)}</b>\n\n<b>3-qadam.</b> Tuman yoki shaharni tanlang:",
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('dist_'))
@safe_handler
def handle_district_chosen(call):
    chat_id = chat_id_of(call)
    state = user_states.get(chat_id)
    if not state or state.get('step') != 'district':
        bot.answer_callback_query(call.id, text="Avval hududni tanlang.")
        return

    dist = District.objects.filter(
        pk=parse_id(call.data, 'dist_'), region_id=state.get('region_id')
    ).first()
    if not dist:
        bot.answer_callback_query(call.id, text="Boshqa viloyatning tumani tanlandi.")
        return

    state['district_id'] = dist.pk
    state['step'] = 'title_desc'
    bot.answer_callback_query(call.id, text=f"{dist.name} tanlandi")

    bot.send_message(
        chat_id,
        f"✅ Tanlandi: <b>{esc(dist.name)}</b>\n\n"
        f"<b>4-qadam.</b> Muammoni qisqacha ifodalang va tavsif yozing:\n"
        f"<i>(Masalan: 4-maktab oldidagi yo‘lda katta o‘ra paydo bo‘lgan, mashinalar qatnovi xavfli bo‘lib qolmoqda)</i>"
    )


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'title_desc')
@safe_handler
def handle_title_desc(message):
    text = (getattr(message, 'text', '') or '').strip()
    if len(text) < 5:
        bot.send_message(message.chat.id, "Iltimos, muammoni batafsilroq bayon qiling:")
        return

    state = user_states[message.chat.id]
    state['title'] = text[:150]
    state['description'] = text[:2000]
    state['step'] = 'location'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📍 Geolokatsiyani yuborish", request_location=True))

    bot.send_message(
        message.chat.id,
        "<b>5-qadam.</b> Aniq manzilni yozing yoki pastdagi <b>«📍 Geolokatsiyani yuborish»</b> tugmasini bosing:",
        reply_markup=markup
    )


@bot.message_handler(content_types=['location'], func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'location')
@safe_handler
def handle_location(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    lat, lng = message.location.latitude, message.location.longitude
    state['lat'], state['lng'] = lat, lng
    state['address'] = f"Geolokatsiya: {lat:.4f}, {lng:.4f}"
    state['step'] = 'photo'

    bot.send_message(
        chat_id,
        "✅ Joylashuv qabul qilindi!\n\n<b>6-qadam.</b> Muammo fotosuratini yuboring (Rasm):",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'location')
@safe_handler
def handle_address_text(message):
    text = (getattr(message, 'text', '') or '').strip()
    if not text:
        bot.send_message(message.chat.id, "Iltimos, manzilni matn shaklida yuboring yoki geolokatsiyadan foydalaning.")
        return

    chat_id = message.chat.id
    state = user_states[chat_id]
    state['address'] = text[:255]
    reg = Region.objects.filter(pk=state.get('region_id')).first()
    state['lat'] = reg.latitude if reg and reg.latitude is not None else 41.2995
    state['lng'] = reg.longitude if reg and reg.longitude is not None else 69.2401
    state['step'] = 'photo'

    bot.send_message(
        chat_id,
        "✅ Manzil qabul qilindi!\n\n<b>6-qadam.</b> Muammo fotosuratini yuboring (Rasm):",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(content_types=['photo'], func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'photo')
@safe_handler
def handle_photo(message):
    chat_id = message.chat.id
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    state = user_states[chat_id]
    state['photo_bytes'] = downloaded_file
    state['step'] = 'phone'

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Telefon raqamimni ulashish", request_contact=True))

    bot.send_message(
        chat_id,
        "✅ Fotosurat yuklandi!\n\n<b>7-qadam.</b> Bog'lanish uchun telefon raqamingizni yuboring:",
        reply_markup=markup
    )


@bot.message_handler(content_types=['contact'], func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'phone')
@safe_handler
def handle_contact(message):
    finish_report_submission(message, message.contact.phone_number)


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'phone')
@safe_handler
def handle_phone_text(message):
    finish_report_submission(message, getattr(message, 'text', '') or '')


def finish_report_submission(message, phone):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state:
        bot.send_message(chat_id, "Xatolik yuz berdi. Boshidan boshlang.", reply_markup=get_main_keyboard())
        return

    required = ('category_id', 'region_id', 'district_id', 'title', 'address')
    if any(not state.get(key) for key in required):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "Ma'lumotlar tugallanmagan. /start buyrug'i bilan qaytadan boshlang.",
                         reply_markup=get_main_keyboard())
        return

    cat = Category.objects.filter(pk=state['category_id']).first()
    reg = Region.objects.filter(pk=state['region_id']).first()
    dist = District.objects.filter(pk=state['district_id'], region_id=state['region_id']).first()
    if not (cat and reg and dist):
        user_states.pop(chat_id, None)
        bot.send_message(chat_id, "Tanlangan kategoriya yoki hudud topilmadi. /start bilan qaytadan boshlang.",
                         reply_markup=get_main_keyboard())
        return

    phone = (phone or '').strip()
    if not PHONE_RE.match(phone):
        bot.send_message(chat_id, "Telefon raqamini to'g'ri formatda yuboring (masalan: +998 90 123 45 67):")
        return

    full_name = message.from_user.full_name or message.from_user.first_name or 'Anonim'
    report = Report(
        title=state['title'],
        description=state['description'],
        category=cat,
        region=reg,
        district=dist,
        address=state['address'],
        latitude=state.get('lat', reg.latitude),
        longitude=state.get('lng', reg.longitude),
        applicant_name=full_name[:150],
        applicant_phone=phone[:30],
        status=Report.STATUS_NEW
    )

    photo_bytes = state.get('photo_bytes')
    if photo_bytes:
        report.image.save(f"bot_report_{chat_id}.jpg", ContentFile(photo_bytes), save=False)
    report.save()

    ReportHistory.objects.create(
        report=report,
        old_status=Report.STATUS_NEW,
        new_status=Report.STATUS_NEW,
        comment="Murojaat Telegram Bot orqali yuborildi."
    )

    user_states.pop(chat_id, None)

    success_text = (
        f"🎉 <b>MUROJAATINGIZ MUVAFFAQIYATLI QABUL QILINDI!</b>\n\n"
        f"📋 Murojaat raqamingiz: <code>{esc(report.tracking_code)}</code>\n"
        f"📌 Sarlavha: {esc(report.title)}\n"
        f"📍 Hudud: {esc(reg.name)}, {esc(dist.name)}\n"
        f"⚡️ Boshlang'ich holati: <b>Yangi</b>\n\n"
        f"Murojaat tez orada mas'ul tashkilotga yo‘naltiriladi. Holatini bilish uchun "
        f"<b>«🔍 Murojaatni tekshirish»</b> tugmasidan foydalanishingiz mumkin."
    )
    bot.send_message(chat_id, success_text, reply_markup=get_main_keyboard())

    if not ADMIN_ID:
        return

    username = getattr(message.from_user, 'username', None) or 'yoq'
    admin_alert = (
        f"🚨 <b>TELEGRAM BOTDAN YANGI MUROJAAT!</b>\n\n"
        f"📋 <b>Raqami:</b> <code>{esc(report.tracking_code)}</code>\n"
        f"📌 <b>Sarlavha:</b> {esc(report.title)}\n"
        f"📁 <b>Kategoriya:</b> {esc(cat.name)}\n"
        f"📍 <b>Hudud:</b> {esc(reg.name)}, {esc(dist.name)}\n"
        f"🏠 <b>Manzil:</b> {esc(report.address)}\n"
        f"👤 <b>Murojaatchi:</b> {esc(full_name)} (@{esc(username)})\n"
        f"📞 <b>Telefon:</b> {esc(phone)}\n"
        f"🕒 <b>Vaqti:</b> {esc(local_dt(report.created_at))}\n\n"
        f"🔗 <b>Saytda ko'rish:</b> {esc(SITE_URL)}/portal/murojaat/{esc(report.tracking_code)}/"
    )

    try:
        if photo_bytes:
            bot.send_photo(ADMIN_ID, photo_bytes, caption=admin_alert)
        else:
            bot.send_message(ADMIN_ID, admin_alert)
    except Exception as exc:
        print(f"Admin alert error: {exc}")


# ---------- 2. Murojaatni tekshirish (Tracking) ----------

@bot.message_handler(func=lambda msg: msg.text == "🔍 Murojaatni tekshirish")
@safe_handler
def ask_tracking_code(message):
    chat_id = message.chat.id
    user_states[chat_id] = {'step': 'tracking_lookup'}
    bot.send_message(
        chat_id,
        "Murojaatingizning noyob raqamini kiriting (masalan: <code>MH-2026-A109F</code>):"
    )


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'tracking_lookup')
@safe_handler
def lookup_report_code(message):
    code = re.sub(r'\s+', '', getattr(message, 'text', '') or '').upper()
    chat_id = message.chat.id
    user_states.pop(chat_id, None)

    if not code:
        bot.send_message(chat_id, "Murojaat raqamini kiriting.", reply_markup=get_main_keyboard())
        return

    report = Report.objects.select_related('category', 'region', 'district').prefetch_related('replies__author') \
        .filter(tracking_code__iexact=code).first()
    if not report:
        bot.send_message(
            chat_id,
            f"❌ <code>{esc(code)}</code> raqamli murojaat topilmadi. Raqam to‘g‘ri kiritilganligini tekshiring.",
            reply_markup=get_main_keyboard()
        )
        return

    status_emojis = {
        Report.STATUS_NEW: "🔵 Yangi",
        Report.STATUS_IN_PROGRESS: "🟡 Ko‘rib chiqilmoqda",
        Report.STATUS_ASSIGNED: "🔷 Mas'ul tashkilotga yuborildi",
        Report.STATUS_RESOLVED: "🟢 Hal qilindi",
        Report.STATUS_REJECTED: "🔴 Rad etildi"
    }
    status_label = status_emojis.get(report.status, report.get_status_display())

    msg = (
        f"📋 <b>MUROJAAT MA'LUMOTLARI:</b>\n\n"
        f"🔢 <b>Raqami:</b> <code>{esc(report.tracking_code)}</code>\n"
        f"📌 <b>Sarlavha:</b> {esc(report.title)}\n"
        f"📁 <b>Kategoriya:</b> {esc(report.category.name)}\n"
        f"📍 <b>Hudud:</b> {esc(report.region.name)}, {esc(report.district.name)}\n"
        f"🏠 <b>Manzil:</b> {esc(report.address)}\n"
        f"🕒 <b>Yuborilgan sana:</b> {esc(local_dt(report.created_at))}\n"
        f"⚡️ <b>Holati:</b> {esc(status_label)}\n"
    )

    replies = list(report.replies.all())
    if replies:
        msg += "\n📢 <b>RASMIY JAVOB:</b>\n"
        for rep in replies:
            author = rep.author.get_display_name() if rep.author else 'Tizim'
            msg += f"• <i>{esc(author)}:</i> {esc(rep.message)}\n"

    msg += f"\n🌐 <b>Batafsil saytda:</b> {esc(SITE_URL)}/report/{esc(report.tracking_code)}/"

    if report.image and os.path.exists(report.image.path):
        with open(report.image.path, 'rb') as photo_file:
            bot.send_photo(chat_id, photo_file, caption=msg, reply_markup=get_main_keyboard())
    else:
        bot.send_message(chat_id, msg, reply_markup=get_main_keyboard())


# ---------- 3. Statistika ----------

@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika")
@safe_handler
def show_platform_stats(message):
    total = Report.objects.count()
    resolved = Report.objects.filter(status=Report.STATUS_RESOLVED).count()
    in_prog = Report.objects.filter(status__in=[Report.STATUS_IN_PROGRESS, Report.STATUS_ASSIGNED]).count()
    new_cnt = Report.objects.filter(status=Report.STATUS_NEW).count()

    stats_text = (
        f"📊 <b>MENING HUDUDIM — Jonli statistika:</b>\n\n"
        f"• Jami qabul qilingan: <b>{total}</b> ta\n"
        f"• 🟢 Hal etilgan: <b>{resolved}</b> ta\n"
        f"• 🟡 Jarayonda: <b>{in_prog}</b> ta\n"
        f"• 🔵 Yangi: <b>{new_cnt}</b> ta\n\n"
        f"<i>Barcha ma'lumotlar real vaqtda bazadan hisoblanadi.</i>"
    )
    bot.send_message(message.chat.id, stats_text, reply_markup=get_main_keyboard())


# ---------- 4. Sayt havolasi va Biz haqimizda ----------

@bot.message_handler(func=lambda msg: msg.text == "🌐 Veb-saytga o'tish")
@safe_handler
def send_website_link(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Veb-platformani ochish", url=SITE_URL))
    bot.send_message(
        message.chat.id,
        "Platformaning to‘liq interaktiv xaritasi va xizmatlaridan foydalanish uchun saytga kiring:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Loyiha haqida")
@safe_handler
def send_about_info(message):
    about_text = (
        f"🇺🇿 <b>«MENING HUDUDIM» Platformasi</b>\n\n"
        f"<b>Shior:</b> <i>«Muammolar ko‘rinadi — yechimlar boshlanadi!»</i>\n\n"
        f"Bu O‘zbekiston fuqarolari va davlat tashkilotlari o‘rtasida ochiq muloqot va "
        f"jamoatchilik nazoratini ta’minlovchi zamonaviy raqamli tizimdir.\n\n"
        f"📞 Yagona Call-markaz: <b>1152</b>\n"
        f"📩 Email: <b>info@meninghududim.uz</b>"
    )
    bot.send_message(message.chat.id, about_text, reply_markup=get_main_keyboard())


# Fallback for unrecognized messages
@bot.message_handler(func=lambda msg: True)
@safe_handler
def default_handler(message):
    bot.send_message(
        message.chat.id,
        "Iltimos, pastdagi menyudan kerakli bo‘limni tanlang 👇",
        reply_markup=get_main_keyboard()
    )


if __name__ == '__main__':
    if not BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN topilmadi: .env faylida tokenni ko'rsating.")
    if not ADMIN_ID:
        print("DIQQAT: TELEGRAM_ADMIN_ID ko'rsatilmagan — admin buyruqlari ishlamaydi.")
    print(f">>> MENING HUDUDIM Telegram Boti ishga tushdi. Sayt: {SITE_URL}")
    bot.infinity_polling(skip_pending=True)
