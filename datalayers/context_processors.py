from .models import Category

def add_navigation(request):
    categories = Category.objects.order_by('name')
    return {'nav_datalayer_categories': categories}
