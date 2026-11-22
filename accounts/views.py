from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from config.security import client_ip, throttle_blocked, throttle_hit, throttle_reset
from .forms import UserRegisterForm, UserLoginForm, UserProfileUpdateForm
from reports.models import Report


def get_safe_next(request):
    """Only allow same-site relative redirects (never a Host-controlled URL)."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url:
        return None
    if not next_url.startswith('/') or next_url.startswith('//') or next_url.startswith('/\\'):
        return None
    return next_url


def register_view(request):
    next_url = get_safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or 'accounts:profile')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"Xush kelibsiz, {user.get_display_name()}! Hisobingiz muvaffaqiyatli yaratildi.")
            login(request, user)
            return redirect(next_url or 'accounts:profile')
        else:
            messages.error(request, "Iltimos, kiritilgan ma'lumotlarni tekshiring.")
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


def login_view(request):
    next_url = get_safe_next(request)
    if request.user.is_authenticated:
        return redirect(next_url or ('dashboard:index' if request.user.is_staff_member else 'accounts:profile'))

    throttle_key = 'login:%s:%s' % (
        client_ip(request),
        (request.POST.get('username') or '').lower()[:64],
    )

    if request.method == 'POST':
        if throttle_blocked(throttle_key, 10, 15 * 60):
            messages.error(
                request,
                "Juda ko'p marta xato kiritdingiz. 15 daqiqa kutib, qaytadan urinib ko'ring."
            )
            form = UserLoginForm(request)
        else:
            form = UserLoginForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                throttle_reset(throttle_key)
                messages.success(request, f"Tizimga muvaffaqiyatli kirdingiz! Xush kelibsiz, {user.get_display_name()}.")
                if next_url:
                    return redirect(next_url)
                if user.is_staff_member:
                    return redirect('dashboard:index')
                return redirect('accounts:profile')
            else:
                throttle_hit(throttle_key, 15 * 60)
                messages.error(request, "Login yoki parol noto'g'ri kiritildi.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('reports:home')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil ma'lumotlaringiz yangilandi.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Xatolik yuz berdi. Formadagi xatolarni to'g'rilang.")
    else:
        form = UserProfileUpdateForm(instance=user)

    user_reports = Report.objects.filter(user=user).select_related('category', 'region', 'district').prefetch_related('replies', 'history').order_by('-created_at')

    context = {
        'form': form,
        'user_reports': user_reports,
        'total_reports': user_reports.count(),
        'resolved_reports': user_reports.filter(status=Report.STATUS_RESOLVED).count(),
        'in_progress_reports': user_reports.filter(status=Report.STATUS_IN_PROGRESS).count(),
        'new_reports': user_reports.filter(status=Report.STATUS_NEW).count(),
    }
    return render(request, 'accounts/profile.html', context)
