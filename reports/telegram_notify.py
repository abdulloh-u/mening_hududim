import html
import os

import requests
from django.conf import settings
from django.utils import timezone

BOT_TOKEN = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
ADMIN_ID = getattr(settings, 'TELEGRAM_ADMIN_ID', 0)
SITE_URL = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')


def _esc(value):
    """User-supplied text must be escaped for Telegram parse_mode=HTML."""
    return html.escape(str(value or ''), quote=False)


def notify_admin_new_report(report):
    """Send an immediate Telegram alert to the admin about a new report."""
    if not BOT_TOKEN or not ADMIN_ID:
        return False

    status_emojis = {
        'new': '🔵 Yangi',
        'in_progress': '🟡 Ko\'rib chiqilmoqda',
        'assigned': '🔷 Biriktirildi',
        'resolved': '🟢 Hal qilindi',
        'rejected': '🔴 Rad etildi'
    }
    status_text = status_emojis.get(report.status, report.get_status_display())
    created_at = timezone.localtime(report.created_at).strftime('%d.%m.%Y %H:%M')
    admin_url = f"{SITE_URL}/portal/murojaat/{report.tracking_code}/"

    caption = (
        f"🚨 <b>YANGI MUROJAAT QABUL QILINDI!</b>\n\n"
        f"📋 <b>Raqami:</b> <code>{_esc(report.tracking_code)}</code>\n"
        f"📌 <b>Sarlavha:</b> {_esc(report.title)}\n"
        f"📁 <b>Kategoriya:</b> {_esc(report.category.name)}\n"
        f"📍 <b>Hudud:</b> {_esc(report.region.name)}, {_esc(report.district.name)}\n"
        f"🏠 <b>Manzil:</b> {_esc(report.address)}\n"
        f"👤 <b>Murojaatchi:</b> {_esc(report.applicant_name or 'Anonim')}\n"
        f"📞 <b>Telefon:</b> {_esc(report.applicant_phone)}\n"
        f"⚡️ <b>Boshlang'ich holati:</b> {_esc(status_text)}\n"
        f"🕒 <b>Sana:</b> {created_at}\n\n"
        f"🔗 <b>Admin Portal:</b> {_esc(admin_url)}"
    )

    url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    url_message = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        if report.image and os.path.exists(report.image.path):
            with open(report.image.path, 'rb') as photo_file:
                resp = requests.post(
                    url_photo,
                    data={'chat_id': ADMIN_ID, 'caption': caption, 'parse_mode': 'HTML'},
                    files={'photo': photo_file},
                    timeout=10,
                )
                return resp.ok
        resp = requests.post(
            url_message,
            json={'chat_id': ADMIN_ID, 'text': caption, 'parse_mode': 'HTML'},
            timeout=10,
        )
        return resp.ok
    except requests.RequestException as exc:
        print(f"Telegram notification error: {exc}")
        return False
