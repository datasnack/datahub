
from django.urls import path, include

from rest_framework import routers, serializers, viewsets

from shapes.models import Shape
from . import views

# Serializers define the API representation.
class ShapeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Shape
        fields = ['name', 'geometry']

# ViewSets define the view behavior.
class ShapeViewSet(viewsets.ModelViewSet):
    queryset = Shape.objects.all()
    serializer_class = ShapeSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'shapes', ShapeViewSet)


urlpatterns = [
    path("shapes/geometry/", views.shape_geometry, name="shape_geometry"),
    path("shapes/bbox/", views.shape_bbox, name="shape_bbox"),

    path('', include(router.urls)),
]
