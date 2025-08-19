from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/incidents/', include('incidents.urls', namespace='incidents')),
    path('api/v1/places/', include('places.urls', namespace='places')),
    path('api/v1/districts/', include('districts.urls', namespace='districts')),
    path('api/v1/proxy/', include('routes.urls', namespace='routes')),
]