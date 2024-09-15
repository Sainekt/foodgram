from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import UserViewSet

app_name = 'api_v1'

Router = DefaultRouter if settings.DEBUG else SimpleRouter

router_v1 = Router()
router_v1.register(r'users', UserViewSet)


urlpatterns = [
    path('', include(router_v1.urls)),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]