from .models import Type

def add_navigation(request):
    types = Type.objects.filter(show_in_nav=True).order_by('position')
    return {'nav_shape_types': types}
