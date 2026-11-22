from .models import Report, Category
from locations.models import Region

def platform_context(request):
    """Global context processor providing platform counters and categories to all templates."""
    total_count = Report.objects.count()
    resolved_count = Report.objects.filter(status=Report.STATUS_RESOLVED).count()
    in_progress_count = Report.objects.filter(status__in=[Report.STATUS_IN_PROGRESS, Report.STATUS_ASSIGNED]).count()
    new_count = Report.objects.filter(status=Report.STATUS_NEW).count()

    return {
        'PLATFORM_NAME': 'MENING HUDUDIM',
        'PLATFORM_SLOGAN': 'Muammolar ko‘rinadi — yechimlar boshlanadi!',
        'global_stats': {
            'total': total_count,
            'resolved': resolved_count,
            'in_progress': in_progress_count,
            'new': new_count,
        },
        'nav_categories': Category.objects.all()[:7],
        'nav_regions': Region.objects.all(),
    }
