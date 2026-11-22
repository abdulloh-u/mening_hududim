import csv
import secrets

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from accounts.models import User
from reports.models import Report, Category, ReportHistory, AdminReply
from locations.models import Region
from .forms import AdminProfileForm, AdminPasswordChangeForm, StaffCreateForm

def staff_check(user):
    return user.is_authenticated and (user.is_staff_member or user.is_staff or user.is_superuser)

def superadmin_check(user):
    return user.is_authenticated and (user.is_superuser or user.role == User.ROLE_SUPERADMIN)


def staff_manager_check(user):
    """Superadmins manage everyone; regional admins manage their own workers."""
    return superadmin_check(user) or (
        user.is_authenticated and user.role == User.ROLE_ADMIN and user.region_id
    )


def filter_reports_for_user(user, queryset):
    """Filters queryset based on user's role and assigned region."""
    # Access is driven by the platform role, not by Django's is_staff flag:
    # portal staff never receives is_staff, so Django admin stays closed to them.
    if user.is_superuser or user.role == User.ROLE_SUPERADMIN:
        return queryset
    # Every other role is region-scoped. A regional admin must never see or
    # edit another region's reports, even by guessing a tracking code.
    if user.region and user.role in [
        User.ROLE_ADMIN, User.ROLE_REGIONAL_STAFF, User.ROLE_SPECIALIST
    ]:
        return queryset.filter(region=user.region)
    return queryset.none()


def safe_csv_cell(value):
    """Neutralise spreadsheet formula injection in exported report fields."""
    text = '' if value is None else str(value)
    if text[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + text
    return text


def apply_report_filters(queryset, request):
    """Shared by the management table and the CSV export."""
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status')
    category_id = request.GET.get('category')
    region_id = request.GET.get('region')
    date_filter = request.GET.get('date')

    if search:
        queryset = queryset.filter(
            Q(tracking_code__icontains=search) |
            Q(title__icontains=search) |
            Q(address__icontains=search) |
            Q(applicant_name__icontains=search) |
            Q(applicant_phone__icontains=search)
        )
    if status in dict(Report.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    if category_id and category_id.isdigit():
        queryset = queryset.filter(category_id=category_id)
    if region_id and region_id.isdigit():
        queryset = queryset.filter(region_id=region_id)

    today = timezone.localdate()
    if date_filter == 'today':
        queryset = queryset.filter(created_at__date=today)
    elif date_filter == 'week':
        queryset = queryset.filter(created_at__date__gte=today - timezone.timedelta(days=7))
    elif date_filter == 'month':
        queryset = queryset.filter(created_at__date__gte=today - timezone.timedelta(days=30))
    return queryset

@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def dashboard_home_view(request):
    """Admin dashboard overview with metrics, Chart.js datasets, and recent activities."""
    user = request.user
    reports = filter_reports_for_user(user, Report.objects.all())

    # Key statistics
    total_count = reports.count()
    new_count = reports.filter(status=Report.STATUS_NEW).count()
    in_progress_count = reports.filter(status=Report.STATUS_IN_PROGRESS).count()
    assigned_count = reports.filter(status=Report.STATUS_ASSIGNED).count()
    resolved_count = reports.filter(status=Report.STATUS_RESOLVED).count()
    rejected_count = reports.filter(status=Report.STATUS_REJECTED).count()

    # Category breakdown for chart
    category_data = (
        reports.values('category__name', 'category__color')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    cat_labels = [c['category__name'] for c in category_data if c['category__name']]
    cat_counts = [c['count'] for c in category_data if c['category__name']]
    cat_colors = [c['category__color'] for c in category_data if c['category__name']]

    # Region breakdown
    region_data = (
        reports.values('region__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:14]
    )
    region_labels = [r['region__name'] for r in region_data if r['region__name']]
    region_counts = [r['count'] for r in region_data if r['region__name']]

    # Recent reports
    recent_reports = reports.select_related('category', 'region', 'district').order_by('-created_at')[:8]

    context = {
        'total_count': total_count,
        'new_count': new_count,
        'in_progress_count': in_progress_count,
        'assigned_count': assigned_count,
        'resolved_count': resolved_count,
        'rejected_count': rejected_count,
        'cat_labels': cat_labels,
        'cat_counts': cat_counts,
        'cat_colors': cat_colors,
        'region_labels': region_labels,
        'region_counts': region_counts,
        'recent_reports': recent_reports,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def dashboard_reports_list_view(request):
    """Detailed management table for reports with advanced filters."""
    user = request.user
    reports = filter_reports_for_user(
        user,
        Report.objects.select_related('category', 'region', 'district', 'assigned_to')
    ).order_by('-created_at')

    # Filters
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status')
    category_id = request.GET.get('category')
    region_id = request.GET.get('region')
    date_filter = request.GET.get('date')
    reports = apply_report_filters(reports, request)

    paginator = Paginator(reports, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'querystring': query_params.urlencode(),
        'categories': Category.objects.all(),
        'regions': Region.objects.all(),
        'status_choices': Report.STATUS_CHOICES,
        'selected_status': status,
        'selected_category': category_id,
        'selected_region': region_id,
        'selected_date': date_filter,
        'search_query': search,
        'total_filtered': reports.count(),
    }
    return render(request, 'dashboard/report_list.html', context)

@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def dashboard_report_detail_view(request, tracking_code):
    """Admin detail view allowing status update, assigning staff/specialists, and posting official replies."""
    user = request.user
    reports = filter_reports_for_user(user, Report.objects.all())
    report = get_object_or_404(
        reports.select_related('category', 'region', 'district', 'user', 'assigned_to')
        .prefetch_related('history', 'replies', 'replies__author'),
        tracking_code=tracking_code
    )

    # Only active, region-bound staff can be assigned. The superadmin is not
    # an assignee and Django-admin staff no longer exists for portal roles.
    staff_members = User.objects.filter(
        role__in=[User.ROLE_SPECIALIST, User.ROLE_REGIONAL_STAFF, User.ROLE_ADMIN],
        is_active=True,
        region=report.region,
    )
    can_finalize = user.is_admin_or_superadmin

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_status':
            new_status = request.POST.get('status')
            comment = request.POST.get('comment', '').strip()
            assigned_to_id = request.POST.get('assigned_to')

            if new_status not in dict(Report.STATUS_CHOICES):
                messages.error(request, "Noto'g'ri holat tanlandi.")
                return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

            if new_status in (Report.STATUS_RESOLVED, Report.STATUS_REJECTED) and not can_finalize:
                messages.error(request, "Murojaatni yakunlash huquqi faqat administratorga tegishli.")
                return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

            if assigned_to_id and (
                not assigned_to_id.isdigit() or
                not staff_members.filter(pk=assigned_to_id).exists()
            ):
                messages.error(request, "Faqat ro'yxatdagi mas'ul xodimni biriktirishingiz mumkin.")
                return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

            resolution_text = request.POST.get('resolution_notes', '').strip()
            if resolution_text and not can_finalize:
                messages.error(request, "Yechim izohini faqat administrator yozishi mumkin.")
                return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

            old_status = report.status
            report.status = new_status
            report.assigned_to_id = assigned_to_id or None

            if resolution_text:
                report.resolution_notes = resolution_text

            report.save()

            ReportHistory.objects.create(
                report=report,
                old_status=old_status,
                new_status=new_status,
                comment=comment or f"Holat '{report.get_status_display()}' ga o'zgartirildi.",
                changed_by=user
            )
            messages.success(request, f"Murojaat holati '{report.get_status_display()}' ga o'zgartirildi.")
            return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

        elif action == 'add_reply':
            if not can_finalize:
                messages.error(request, "Rasmiy javob berish huquqi faqat administratorga tegishli.")
                return redirect('dashboard:report_detail', tracking_code=report.tracking_code)
            reply_message = request.POST.get('reply_message', '').strip()
            if reply_message:
                AdminReply.objects.create(
                    report=report,
                    author=user,
                    message=reply_message
                )
                messages.success(request, "Rasmiy javob muvaffaqiyatli saqlandi va fuqaroga ko'rinadi.")
            else:
                messages.error(request, "Javob matni bo'sh bo'lishi mumkin emas.")
            return redirect('dashboard:report_detail', tracking_code=report.tracking_code)

    context = {
        'report': report,
        'status_choices': Report.STATUS_CHOICES,
        'staff_members': staff_members,
    }
    return render(request, 'dashboard/report_detail.html', context)

# --- Staff and Admin Management ---
@login_required
@user_passes_test(staff_manager_check, login_url='accounts:login')
def dashboard_staff_list_view(request):
    """Superadmins see everyone; a regional admin sees only their own workers."""
    staff_members = User.objects.filter(
        role__in=[User.ROLE_ADMIN, User.ROLE_REGIONAL_STAFF, User.ROLE_SPECIALIST, User.ROLE_SUPERADMIN]
    ).select_related('region')

    if not superadmin_check(request.user):
        staff_members = staff_members.filter(region=request.user.region)

    staff_members = staff_members.order_by('role', 'username')
    return render(request, 'dashboard/staff_list.html', {
        'staff_members': staff_members,
        'total_staff': staff_members.count(),
        'is_regional_admin': not superadmin_check(request.user),
    })


@login_required
@user_passes_test(staff_manager_check, login_url='accounts:login')
def dashboard_staff_create_view(request):
    """Create a worker. A regional admin is limited to their own region."""
    is_superadmin = superadmin_check(request.user)
    fixed_region = None if is_superadmin else request.user.region

    if request.method == 'POST':
        form = StaffCreateForm(
            request.POST, is_superadmin=is_superadmin, fixed_region=fixed_region
        )
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            if fixed_region:
                new_user.region = fixed_region  # cannot be tampered with via POST
            # Django admin site is reserved for superadmins. Portal access comes
            # from the platform role, not from Django's is_staff flag.
            new_user.is_staff = False
            new_user.is_superuser = False
            new_user.is_active = True  # regional admin approves on creation
            new_user.save()

            messages.success(
                request,
                f"Yangi xodim '{new_user.get_display_name()}' ({new_user.get_role_display()}) "
                f"— {new_user.region.name} muvaffaqiyatli qo'shildi va tasdiqlandi!"
            )
            return redirect('dashboard:staff_list')
        else:
            messages.error(request, "Ma'lumotlarni to'g'ri to'ldiring.")
    else:
        form = StaffCreateForm(is_superadmin=is_superadmin, fixed_region=fixed_region)

    return render(request, 'dashboard/staff_create.html', {
        'form': form,
        'is_regional_admin': not is_superadmin,
        'fixed_region': fixed_region,
    })


@login_required
@user_passes_test(superadmin_check, login_url='accounts:login')
def dashboard_region_admins_view(request):
    """Create and review one administrator per region — superadmins only."""
    regions = Region.objects.order_by('order')
    created_credentials = []

    def admin_map():
        return {
            admin.region_id: admin
            for admin in User.objects.filter(
                role=User.ROLE_ADMIN, region__isnull=False
            ).select_related('region')
        }

    def create_admin(region):
        base = 'admin_' + region.code.lower()
        username = base
        suffix = 1
        while User.objects.filter(username__iexact=username).exists():
            suffix += 1
            username = f'{base}_{suffix}'

        password = secrets.token_urlsafe(18)
        admin = User.objects.create_user(
            username=username,
            password=password,
            full_name=f'{region.name} administratori',
            role=User.ROLE_ADMIN,
            region=region,
            is_staff=False,
            is_superuser=False,
            is_active=True,
        )
        return {
            'region': region.name,
            'username': admin.username,
            'password': password,
        }

    if request.method == 'POST':
        action = request.POST.get('action')
        admins = admin_map()
        if action == 'create_missing':
            for region in regions:
                if region.id not in admins:
                    created_credentials.append(create_admin(region))
            if created_credentials:
                messages.success(
                    request,
                    f"{len(created_credentials)} ta viloyat administratori yaratildi. "
                    "Parollarni pastdan nusxalab oling — ular faqat bir marta ko'rsatiladi."
                )
            else:
                messages.info(request, "Barcha viloyatlarda administrator allaqachon bor.")
        elif action == 'create_one':
            region_id = request.POST.get('region_id', '')
            region = regions.filter(pk=region_id).first() if region_id.isdigit() else None
            if region is None:
                messages.error(request, "Noto'g'ri viloyat tanlandi.")
            elif region.id in admins:
                messages.info(request, f"{region.name} uchun administrator allaqachon mavjud.")
            else:
                created_credentials.append(create_admin(region))
                messages.success(
                    request,
                    f"{region.name} administratori yaratildi. Parolni pastdan nusxalab oling."
                )
        else:
            messages.error(request, "Noma'lum amal.")

    rows = []
    admins = admin_map()
    for region in regions:
        rows.append({
            'region': region,
            'admin': admins.get(region.id),
        })

    context = {
        'rows': rows,
        'filled_count': sum(1 for row in rows if row['admin']),
        'total_count': len(rows),
        'created_credentials': created_credentials,
    }
    return render(request, 'dashboard/region_admins.html', context)


@require_POST
@login_required
@user_passes_test(staff_manager_check, login_url='accounts:login')
def dashboard_staff_toggle_view(request, user_id):
    """Activate/deactivate a worker. Regional admins are limited to their region."""
    if superadmin_check(request.user):
        target_user = get_object_or_404(User, id=user_id)
    else:
        target_user = get_object_or_404(
            User,
            id=user_id,
            region=request.user.region,
            role__in=[User.ROLE_REGIONAL_STAFF, User.ROLE_SPECIALIST],
        )
    if target_user == request.user:
        messages.error(request, "O'zingizni o'chira olmaysiz.")
        return redirect('dashboard:staff_list')

    action = request.POST.get('action')
    if action not in {'toggle_active', 'delete'}:
        messages.error(request, "Noma'lum amal.")
        return redirect('dashboard:staff_list')

    is_super = target_user.is_superuser or target_user.role == User.ROLE_SUPERADMIN
    if is_super:
        other_superadmins = User.objects.filter(
            Q(is_superuser=True) | Q(role=User.ROLE_SUPERADMIN)
        ).exclude(pk=target_user.pk).filter(is_active=True).count()
        if other_superadmins == 0 and (action == 'delete' or target_user.is_active):
            messages.error(request, "Tizimda kamida bitta faol bosh administrator qolishi kerak.")
            return redirect('dashboard:staff_list')

    if action == 'toggle_active':
        target_user.is_active = not target_user.is_active
        target_user.save()
        status_word = "faollashtirildi" if target_user.is_active else "bloklandi"
        messages.success(request, f"'{target_user.get_display_name()}' hisobi {status_word}.")
    else:
        target_user.delete()
        messages.success(request, "Xodim tizimdan o'chirildi.")

    return redirect('dashboard:staff_list')

# --- Admin Profile & Password Settings ---
@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def admin_settings_view(request):
    """Allows admin/staff to change their own username, profile info, and password."""
    user = request.user
    profile_form = AdminProfileForm(instance=user)
    password_form = AdminPasswordChangeForm(user=user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'update_profile':
            profile_form = AdminProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil ma'lumotlaringiz (login/ism/telefon) muvaffaqiyatli yangilandi!")
                return redirect('dashboard:settings')
            else:
                messages.error(request, "Profilni yangilashda xatolik yuz berdi.")

        elif form_type == 'change_password':
            password_form = AdminPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                new_pass = password_form.cleaned_data['new_password']
                user.set_password(new_pass)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Parolingiz muvaffaqiyatli o'zgartirildi!")
                return redirect('dashboard:settings')
            else:
                messages.error(request, "Parolni o'zgartirishda xatolik yuz berdi. Formani tekshiring.")

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'dashboard/settings.html', context)

@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def export_reports_csv(request):
    """Exports filtered reports as CSV format."""
    user = request.user
    reports = filter_reports_for_user(user, Report.objects.select_related('category', 'region', 'district'))
    reports = apply_report_filters(reports, request)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="mening_hududim_murojaatlar.csv"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)
    writer.writerow([
        'Raqami', 'Sarlavha', 'Kategoriya', 'Viloyat', 'Tuman',
        'Aniq manzil', 'Holat', 'Murojaatchi', 'Telefon', 'Sana'
    ])

    for r in reports:
        writer.writerow([
            safe_csv_cell(r.tracking_code),
            safe_csv_cell(r.title),
            safe_csv_cell(r.category.name),
            safe_csv_cell(r.region.name),
            safe_csv_cell(r.district.name),
            safe_csv_cell(r.address),
            safe_csv_cell(r.get_status_display()),
            safe_csv_cell(r.applicant_name or (r.user.get_display_name() if r.user else "Anonim")),
            safe_csv_cell(r.applicant_phone),
            safe_csv_cell(timezone.localtime(r.created_at).strftime('%Y-%m-%d %H:%M'))
        ])

    return response

@login_required
@user_passes_test(staff_check, login_url='accounts:login')
def dashboard_statistics_view(request):
    """Analytics view with comprehensive charts and breakdowns."""
    user = request.user
    reports = filter_reports_for_user(user, Report.objects.all())

    status_counts = {
        'new': reports.filter(status=Report.STATUS_NEW).count(),
        'in_progress': reports.filter(status=Report.STATUS_IN_PROGRESS).count(),
        'assigned': reports.filter(status=Report.STATUS_ASSIGNED).count(),
        'resolved': reports.filter(status=Report.STATUS_RESOLVED).count(),
        'rejected': reports.filter(status=Report.STATUS_REJECTED).count(),
    }

    region_breakdown = (
        reports.values('region__name')
        .annotate(
            total=Count('id'),
            resolved=Count('id', filter=Q(status=Report.STATUS_RESOLVED)),
            pending=Count('id', filter=Q(status__in=[Report.STATUS_NEW, Report.STATUS_IN_PROGRESS, Report.STATUS_ASSIGNED]))
        )
        .order_by('-total')
    )

    category_breakdown = (
        reports.values('category__name', 'category__color')
        .annotate(total=Count('id'), resolved=Count('id', filter=Q(status=Report.STATUS_RESOLVED)))
        .order_by('-total')
    )

    context = {
        'status_counts': status_counts,
        'region_breakdown': region_breakdown,
        'category_breakdown': category_breakdown,
        'total_reports': reports.count(),
    }
    return render(request, 'dashboard/statistics.html', context)
