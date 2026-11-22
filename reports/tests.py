from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from locations.models import Region, District
from reports.models import Category, Report, ReportHistory, AdminReply
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

def get_test_image():
    file = BytesIO()
    image = Image.new('RGB', (100, 100), 'blue')
    image.save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')

class ReportsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.region = Region.objects.create(name="Toshkent shahri", code="TS")
        self.district = District.objects.create(name="Chilonzor", region=self.region)
        self.category = Category.objects.create(name="Yo'llar va transport", icon="fa-solid fa-road", color="#2563EB")

        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
            full_name="Test User",
            phone="+998901234567",
            role=User.ROLE_CITIZEN
        )

        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="password123",
            full_name="Staff User",
            role=User.ROLE_ADMIN,
            is_staff=True
        )

        self.report = Report.objects.create(
            title="Test muammo",
            description="Test tavsif matni",
            category=self.category,
            region=self.region,
            district=self.district,
            address="Navoiy ko'chasi 1-uy",
            latitude=41.2995,
            longitude=69.2401,
            image=get_test_image(),
            applicant_name="Test User",
            applicant_phone="+998901234567",
            status=Report.STATUS_NEW
        )

    def test_home_page_status_code(self):
        response = self.client.get(reverse('reports:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MENING HUDUDIM")
        self.assertContains(response, "Test muammo")

    def test_report_detail_view(self):
        response = self.client.get(reverse('reports:detail', kwargs={'tracking_code': self.report.tracking_code}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.report.tracking_code)
        self.assertContains(response, "Test muammo")

    def test_report_list_view(self):
        response = self.client.get(reverse('reports:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test muammo")

    def test_report_create_view_post(self):
        data = {
            'title': 'Yangi chuqur yo\'l',
            'category': self.category.id,
            'region': self.region.id,
            'district': self.district.id,
            'address': 'Amir Temur shoh ko\'chasi',
            'latitude': 41.3111,
            'longitude': 69.2797,
            'applicant_name': 'Rustam',
            'applicant_phone': '+998909998877',
            'description': 'Katta o\'ra hosil bo\'lgan.',
            'image': get_test_image(),
        }
        response = self.client.post(reverse('reports:create'), data)
        self.assertEqual(response.status_code, 302)

        # Check in DB
        created_report = Report.objects.filter(title='Yangi chuqur yo\'l').first()
        self.assertIsNotNone(created_report)
        self.assertTrue(created_report.tracking_code.startswith("MH-2026-"))
        self.assertEqual(created_report.status, Report.STATUS_NEW)

        # Check history was created
        history = ReportHistory.objects.filter(report=created_report)
        self.assertTrue(history.exists())

    def test_reports_api_geojson(self):
        response = self.client.get(reverse('reports:api_geojson'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('reports', data)
        self.assertEqual(len(data['reports']), 1)
        self.assertEqual(data['reports'][0]['tracking_code'], self.report.tracking_code)

    def test_districts_api(self):
        response = self.client.get(reverse('locations:districts_by_region', kwargs={'region_id': self.region.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('districts', data)
        self.assertEqual(len(data['districts']), 1)
        self.assertEqual(data['districts'][0]['name'], "Chilonzor")

    def test_tracking_lookup(self):
        response = self.client.get(reverse('reports:track') + f"?code={self.report.tracking_code}")
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.report.tracking_code, response.url)


class RegionalStaffAccessTestCase(TestCase):
    def setUp(self):
        self.region = Region.objects.create(name="Toshkent shahri", code="TS")
        self.other_region = Region.objects.create(name="Samarqand viloyati", code="SQ")
        self.district = District.objects.create(name="Chilonzor", region=self.region)
        self.other_district = District.objects.create(name="Samarqand shahri", region=self.other_region)
        self.category = Category.objects.create(name="Yo'llar", icon="fa-road", color="#2563EB")

        self.staff = User.objects.create_user(
            username="region_staff",
            password="password123",
            full_name="Hududiy xodim",
            phone="+998901234567",
            role=User.ROLE_REGIONAL_STAFF,
            region=self.region,
            is_staff=True,
        )

        self.own_report = Report.objects.create(
            title="O'z hududidagi muammo", description="Tavsif", category=self.category,
            region=self.region, district=self.district, address="Manzil 1",
            latitude=41.3, longitude=69.2, image=get_test_image(),
            applicant_phone="+998901111111"
        )
        self.foreign_report = Report.objects.create(
            title="Boshqa hududdagi muammo", description="Tavsif", category=self.category,
            region=self.other_region, district=self.other_district, address="Manzil 2",
            latitude=39.6, longitude=66.9, image=get_test_image(),
            applicant_phone="+998901111111"
        )

    def test_regional_staff_sees_only_own_region(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 1)

        response = self.client.get(reverse('dashboard:report_list'))
        self.assertEqual(response.context['total_filtered'], 1)

        response = self.client.get(reverse(
            'dashboard:report_detail',
            kwargs={'tracking_code': self.foreign_report.tracking_code}
        ))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse(
            'dashboard:report_detail',
            kwargs={'tracking_code': self.own_report.tracking_code}
        ))
        self.assertEqual(response.status_code, 200)
