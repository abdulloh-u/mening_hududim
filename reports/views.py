import json
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.urls import reverse
from django.utils import timezone
from config.security import client_ip, throttle_blocked, throttle_hit
from .models import Report, Category, ReportHistory
from .forms import ReportCreateForm
from locations.models import Region, District
from .telegram_notify import notify_admin_new_report

def home_view(request):
    """Main landing page with hero, statistics, categories, recent reports, and workflow steps."""
    recent_reports = Report.objects.select_related('category', 'region', 'district').order_by('-created_at')[:6]
    categories = Category.objects.annotate(total_reports=Count('reports')).order_by('order')

    stats = {
        'total': Report.objects.count(),
        'resolved': Report.objects.filter(status=Report.STATUS_RESOLVED).count(),
        'in_progress': Report.objects.filter(status__in=[Report.STATUS_IN_PROGRESS, Report.STATUS_ASSIGNED]).count(),
        'new': Report.objects.filter(status=Report.STATUS_NEW).count(),
    }

    context = {
        'recent_reports': recent_reports,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'home.html', context)

def report_create_view(request):
    """Citizen report submission view with client & server-side validation and map picker."""
    if request.method == 'POST':
        form = ReportCreateForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.user = request.user
                if not report.applicant_name:
                    report.applicant_name = request.user.get_display_name()
                if not report.applicant_phone and request.user.phone:
                    report.applicant_phone = request.user.phone
            report.save()

            # Record initial history log
            ReportHistory.objects.create(
                report=report,
                old_status=Report.STATUS_NEW,
                new_status=Report.STATUS_NEW,
                comment="Murojaat fuqaro tomonidan platformaga kiritildi.",
                changed_by=request.user if request.user.is_authenticated else None
            )

            # Send Telegram notification to Admin
            try:
                notify_admin_new_report(report)
            except Exception:
                pass

            messages.success(
                request,
                f"Murojaatingiz qabul qilindi! Murojaat raqami: {report.tracking_code}"
            )
            return redirect('reports:success', tracking_code=report.tracking_code)
        else:
            messages.error(request, "Iltimos, shakldagi xatoliklarni to'g'rilang.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['applicant_name'] = request.user.get_display_name()
            initial_data['applicant_phone'] = request.user.phone
        form = ReportCreateForm(initial=initial_data)

    context = {
        'form': form,
        'regions': Region.objects.all(),
        'categories': Category.objects.all(),
    }
    return render(request, 'reports/create.html', context)

def report_success_view(request, tracking_code):
    """Confirmation page with tracking code and actions."""
    report = get_object_or_404(Report.objects.select_related('category', 'region', 'district'), tracking_code=tracking_code)
    return render(request, 'reports/success.html', {'report': report})

def report_detail_view(request, tracking_code):
    """Detailed view of a report showing photos, coordinates, history, and official replies."""
    report = get_object_or_404(
        Report.objects.select_related('category', 'region', 'district', 'assigned_to')
        .prefetch_related('history', 'replies', 'replies__author'),
        tracking_code=tracking_code
    )
    return render(request, 'reports/detail.html', {'report': report})

def report_list_view(request):
    """List of all reports with filters and pagination."""
    reports = Report.objects.select_related('category', 'region', 'district').order_by('-created_at')

    # Filters
    search_query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    region_id = request.GET.get('region')
    status = request.GET.get('status')

    if search_query:
        reports = reports.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(tracking_code__iexact=search_query)
        )
    if category_id and category_id.isdigit():
        reports = reports.filter(category_id=category_id)
    if region_id and region_id.isdigit():
        reports = reports.filter(region_id=region_id)
    if status in dict(Report.STATUS_CHOICES):
        reports = reports.filter(status=status)

    paginator = Paginator(reports, 9)
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
        'search_query': search_query,
        'selected_category': category_id,
        'selected_region': region_id,
        'selected_status': status,
        'total_found': reports.count(),
    }
    return render(request, 'reports/list.html', context)

def report_map_view(request):
    """Full-page interactive Leaflet map of all reports in Uzbekistan."""
    categories = Category.objects.all()
    regions = Region.objects.annotate(report_count=Count('reports')).order_by('name')
    return render(request, 'reports/map.html', {
        'categories': categories,
        'regions': regions,
        'status_choices': Report.STATUS_CHOICES,
    })

def reports_api_geojson(request):
    """API endpoint providing reports data for Leaflet map markers."""
    reports = Report.objects.select_related('category', 'region', 'district').all()

    # Apply filters if provided
    category_id = request.GET.get('category')
    region_id = request.GET.get('region')
    status = request.GET.get('status')

    if category_id and category_id.isdigit():
        reports = reports.filter(category_id=category_id)
    if region_id and region_id.isdigit():
        reports = reports.filter(region_id=region_id)
    if status in dict(Report.STATUS_CHOICES):
        reports = reports.filter(status=status)

    data = []
    for r in reports:
        data.append({
            'id': r.id,
            'tracking_code': r.tracking_code,
            'title': r.title,
            'category': r.category.name,
            'category_color': r.category.color,
            'category_icon': r.category.icon,
            'status': r.status,
            'status_display': r.get_status_display(),
            'status_badge': r.status_badge_class,
            'region': r.region.name,
            'district': r.district.name,
            'address': r.address,
            'lat': r.latitude,
            'lng': r.longitude,
            'image_url': r.image.url if r.image else None,
            'detail_url': reverse('reports:detail', kwargs={'tracking_code': r.tracking_code}),
            'created_at': timezone.localtime(r.created_at).strftime('%d.%m.%Y %H:%M'),
        })

    return JsonResponse({'reports': data, 'total': len(data)})


def normalize_region_name(name):
    """Normalise apostrophe/diacritic variants so GeoJSON names match the DB."""
    text = unicodedata.normalize('NFKD', name or '')
    for char in ('ʻ', 'ʼ', '’', '‘', '`', '´'):
        text = text.replace(char, "'")
    text = re.sub(r'\bsh\.\s*$', 'shahri', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip().lower()


def regions_geojson_view(request):
    """Real administrative map of Uzbekistan: state border + all 14 regions.

    Each region feature is enriched with its database id and report count so the
    map can filter/zoom on click without relying on fragile name matching.
    """
    geo_dir = Path(settings.BASE_DIR) / 'static' / 'geo'

    def load(filename):
        try:
            with (geo_dir / filename).open(encoding='utf-8') as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {'type': 'FeatureCollection', 'features': []}

    regions_layer = load('uzbekistan_regions.geojson')
    country_layer = load('uzbekistan_country.geojson')

    counts = dict(Report.objects.values_list('region_id').annotate(total=Count('id')))
    regions_by_name = {
        normalize_region_name(region.name): region for region in Region.objects.all()
    }

    for feature in regions_layer.get('features', []):
        props = feature.setdefault('properties', {})
        name = props.get('ADM1_UZ') or props.get('ADM1_EN') or ''
        region = regions_by_name.get(normalize_region_name(name))
        props['name_uz'] = name
        props['region_id'] = region.id if region else None
        props['region_name'] = region.name if region else name
        props['report_count'] = counts.get(region.id, 0) if region else 0

    return JsonResponse({'regions': regions_layer, 'country': country_layer})


def report_track_view(request):
    """Direct lookup search for a report by tracking code."""
    code = re.sub(r'\s+', '', request.GET.get('code', '')).upper() if request.GET.get('code') else ''
    throttle_key = 'track:%s' % client_ip(request)
    if code and throttle_blocked(throttle_key, 30, 60 * 60):
        messages.error(request, "Juda ko'p qidiruv qildingiz. Bir oz kutib, qaytadan urinib ko'ring.")
        return render(request, 'track.html', {'searched_code': code})
    if code:
        throttle_hit(throttle_key, 60 * 60)
        report = Report.objects.filter(tracking_code__iexact=code).first()
        if report:
            return redirect('reports:detail', tracking_code=report.tracking_code)
        messages.error(request, f"'{code}' raqamli murojaat topilmadi. Raqamni qayta tekshiring.")

    return render(request, 'track.html', {'searched_code': code})

def about_view(request):
    """About page introducing the MENING HUDUDIM initiative and FAQs."""
    return render(request, 'about.html')

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
