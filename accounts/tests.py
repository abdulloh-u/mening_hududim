from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User

class AccountsAndDashboardSecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.citizen = User.objects.create_user(
            username="citizen_test",
            password="password123",
            role=User.ROLE_CITIZEN
        )
        self.admin = User.objects.create_user(
            username="admin_test",
            password="password123",
            role=User.ROLE_ADMIN,
            is_staff=True
        )

    def test_registration(self):
        data = {
            'username': 'newuser',
            'full_name': 'New Citizen',
            'phone': '+998901112233',
            'email': 'new@test.uz',
            'password': 'safePassword123',
            'password_confirm': 'safePassword123'
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_and_logout(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'citizen_test',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

        # Profile access
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "citizen_test")

        # Logout must be a POST request (CSRF-safe)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 405)
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_access_control(self):
        # Anonymous user cannot access portal
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

        # Regular citizen is redirected away
        self.client.login(username='citizen_test', password='password123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # Admin user CAN access portal
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Boshqaruv Paneli")

    def test_csv_export(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('dashboard:export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="mening_hududim_murojaatlar.csv"', response['Content-Disposition'])
