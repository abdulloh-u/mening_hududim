import os
import secrets

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from locations.models import Region, District
from reports.models import Category


def run_seed():
    print(">>> O'zbekiston hududlari va kategoriyalari yangilanmoqda...")

    # 1. 14 Regions of Uzbekistan with Center Coordinates and Zooms
    regions_info = [
        ("Toshkent shahri", "TS", 41.2995, 69.2401, 12, [
            "Yunusobod tumani", "Chilonzor tumani", "Mirzo Ulug'bek tumani",
            "Yakkasaroy tumani", "Shayxontohur tumani", "Mirobod tumani",
            "Olmazor tumani", "Uchtepa tumani", "Sergeli tumani",
            "Yashnobod tumani", "Bektemir tumani", "Yangihayot tumani"
        ]),
        ("Toshkent viloyati", "TV", 41.2213, 69.8597, 10, [
            "Chirchiq shahri", "Angren shahri", "Olmaliq shahri", "Yangiyo'l shahri",
            "Qibray tumani", "Zangiota tumani", "Bo'stonliq tumani", "Parkent tumani", "Bekobod shahri"
        ]),
        ("Samarqand viloyati", "SAM", 39.6542, 66.9597, 10, [
            "Samarqand shahri", "Kattaqo'rg'on shahri", "Pastdarg'om tumani",
            "Urgut tumani", "Payariq tumani", "Jomboy tumani", "Toyloq tumani", "Ishtixon tumani"
        ]),
        ("Farg'ona viloyati", "FAR", 40.3864, 71.7864, 10, [
            "Farg'ona shahri", "Marg'ilon shahri", "Qo'qon shahri", "Quvasoy shahri",
            "Oltiariq tumani", "Rishton tumani", "Bag'dod tumani", "Uchko'prik tumani"
        ]),
        ("Andijon viloyati", "AND", 40.7821, 72.3442, 11, [
            "Andijon shahri", "Asaka tumani", "Shahrixon tumani", "Xonobod shahri",
            "Baliqchi tumani", "Izboskan tumani", "Qo'rg'ontepa tumani", "Marhamat tumani"
        ]),
        ("Namangan viloyati", "NAM", 40.9983, 71.6726, 11, [
            "Namangan shahri", "Chortoq tumani", "Chust tumani", "Kosonsoy tumani",
            "Pop tumani", "To'raqo'rg'on tumani", "Uchqo'rg'on tumani", "Yangiqo'rg'on tumani"
        ]),
        ("Buxoro viloyati", "BUX", 39.7747, 64.4086, 10, [
            "Buxoro shahri", "Kogon shahri", "G'ijduvon tumani", "Vobkent tumani",
            "Jondor tumani", "Qorovulbozor tumani", "Romitan tumani", "Shofirkon tumani"
        ]),
        ("Xorazm viloyati", "XOR", 41.5545, 60.6315, 10, [
            "Urganch shahri", "Xiva shahri", "Bog'ot tumani", "Gurlan tumani",
            "Xonqa tumani", "Hazorasp tumani", "Shovot tumani", "Yangiariq tumani"
        ]),
        ("Qashqadaryo viloyati", "QASH", 38.8612, 65.7847, 9, [
            "Qarshi shahri", "Shahrisabz shahri", "Kitob tumani", "Koson tumani",
            "G'uzor tumani", "Dehqonobod tumani", "Yakkabog' tumani", "Chiroqchi tumani"
        ]),
        ("Surxondaryo viloyati", "SUR", 37.2242, 67.2783, 9, [
            "Termiz shahri", "Denov tumani", "Boysun tumani", "Sherobod tumani",
            "Jarqo'rg'on tumani", "Sho'rchi tumani", "Qumqo'rg'on tumani"
        ]),
        ("Navoiy viloyati", "NAV", 40.0844, 65.3792, 9, [
            "Navoiy shahri", "Zarafshon shahri", "Karmana tumani", "Qiziltepa tumani",
            "Nurota tumani", "Uchquduq tumani", "Xatirchi tumani"
        ]),
        ("Jizzax viloyati", "JIZ", 40.1158, 67.8422, 10, [
            "Jizzax shahri", "Do'stlik tumani", "Zomin tumani", "Zarbdor tumani",
            "G'allaorol tumani", "Sharof Rashidov tumani", "Paxtakor tumani"
        ]),
        ("Sirdaryo viloyati", "SIR", 40.4983, 68.7842, 10, [
            "Guliston shahri", "Yangiyer shahri", "Shirin shahri", "Boyovut tumani",
            "Mirzaobod tumani", "Oqoltin tumani", "Sardoba tumani", "Sayxunobod tumani"
        ]),
        ("Qoraqalpog'iston Respublikasi", "QR", 42.4619, 59.6166, 8, [
            "Nukus shahri", "Beruniy tumani", "To'rtko'l tumani", "Xo'jayli tumani",
            "Qo'ng'irot tumani", "Chimboy tumani", "Mo'ynoq tumani", "Amudaryo tumani"
        ]),
    ]

    for order_idx, (r_name, r_code, lat, lng, zoom, districts) in enumerate(regions_info, start=1):
        reg, _ = Region.objects.update_or_create(
            name=r_name,
            defaults={
                'code': r_code,
                'order': order_idx,
                'latitude': lat,
                'longitude': lng,
                'zoom_level': zoom
            }
        )
        for d_name in districts:
            District.objects.get_or_create(name=d_name, region=reg)

    print(f"Regions updated: {Region.objects.count()} regions, {District.objects.count()} districts.")

    # 2. Categories
    categories_data = [
        ("Yo'llar va transport", "fa-solid fa-road", "#2563EB", 1, "Buzilgan yo'llar, chuqurlar, svetofor va yo'l belgilari nosozligi"),
        ("Ichimlik suvi ta'minoti", "fa-solid fa-faucet-drip", "#0284C7", 2, "Ichimlik suvi yo'qligi, quvur yorilishi, suv sifati pastligi"),
        ("Elektr va ko'cha chiroqlari", "fa-solid fa-lightbulb", "#EAB308", 3, "Ko'cha chiroqlari yonmasligi, sim yog'ochlar sinishi, elektr uzilishlari"),
        ("Chiqindilar va tozalik", "fa-solid fa-trash-can", "#10B981", 4, "Noqonuniy chiqindixonalar, o'z vaqtida olib ketilmagan axlatlar"),
        ("Kanalizatsiya va issiqlik", "fa-solid fa-water", "#6366F1", 5, "Kanalizatsiya to'lib ketishi, quvurlardagi nosozliklar, issiqlik ta'minoti"),
        ("Ekologiya va ko'kalamzorlashtirish", "fa-solid fa-tree", "#059669", 6, "Daraxtlarning noqonuniy kesilishi, yashil hududlarning payhon qilinishi"),
        ("Jamoat joylari va xavfsizlik", "fa-solid fa-shield-halved", "#DC2626", 7, "Bolalar maydonchalari xavfsizligi, jamoat mulkiga zarar yetkazilishi"),
    ]

    for name, icon, color, order, desc in categories_data:
        Category.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'color': color, 'order': order, 'description': desc}
        )

    print(f"Kategoriyalar: {Category.objects.count()} ta.")

    # 3. Doimiy boshqaruv hisoblari (demo hisob emas).
    # Hech qanday parol kodga yozilmaydi: yangi o'rnatishda SEED_ABU_PASSWORD
    # berilsa shundan, aks holda tasodifiy parol ishlatiladi va bir marta chop etiladi.
    abu, created = User.objects.get_or_create(username='Abu')
    abu_password = None
    if created:
        abu_password = os.environ.get('SEED_ABU_PASSWORD') or secrets.token_urlsafe(18)
        abu.set_password(abu_password)
        abu.full_name = 'Abu'
    abu.role = User.ROLE_SUPERADMIN
    abu.is_staff = True
    abu.is_superuser = True
    abu.is_active = True
    abu.save()

    chief, chief_created = User.objects.get_or_create(username='bosh_admin')
    chief_password = None
    if chief_created:
        chief_password = secrets.token_urlsafe(18)
        chief.set_password(chief_password)
        chief.full_name = 'Bosh Administrator'
    chief.role = User.ROLE_SUPERADMIN
    chief.is_staff = True
    chief.is_superuser = True
    chief.is_active = True
    chief.save()

    # Old demo accounts must never remain in the system.
    User.objects.filter(username__in=[
        'toshkent_staff', 'fuqaro', 'samarqand_staff', 'sobir_usta', 'adminaa'
    ]).delete()

    if abu_password:
        print(f"Yangi Abu paroli: Abu / {abu_password} — saqlab qoling!")
    if chief_password:
        print(f"Yangi Bosh Admin paroli: bosh_admin / {chief_password} — saqlab qoling!")
    print("Viloyat adminlari va ishchilar portal orqali qo'shiladi.")
    print("Tayyor. Demo murojaatlar va sinov foydalanuvchilar yo'q — "
          "tizim faqat haqiqiy ma'lumotlar bilan ishlaydi.")


if __name__ == '__main__':
    run_seed()
