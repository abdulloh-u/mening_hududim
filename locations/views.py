from django.http import JsonResponse
from .models import District, Region

def get_districts_by_region(request, region_id):
    """Returns JSON list of districts and region center coords for a given region ID."""
    try:
        region = Region.objects.get(id=region_id)
        region_info = {
            'id': region.id,
            'name': region.name,
            'lat': region.latitude,
            'lng': region.longitude,
            'zoom': region.zoom_level
        }
    except Region.DoesNotExist:
        region_info = None

    districts = District.objects.filter(region_id=region_id).values('id', 'name', 'latitude', 'longitude').order_by('name')
    return JsonResponse({
        'region': region_info,
        'districts': list(districts)
    })
