from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter
from .views import (
    UserViewSet,
    TagsView,
    IngredientsView,
    RecipeViewSet,
    ShortLinkSerializer,
)
app_name = 'api_v1'

Router = DefaultRouter if settings.DEBUG else SimpleRouter

router_v1 = Router()
router_v1.register(r'users', UserViewSet)
router_v1.register(r'tags', TagsView)
router_v1.register(r'ingredients', IngredientsView, basename='ingredients')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('', include(router_v1.urls), name='routers'),
    path('auth/', include('djoser.urls.authtoken')),
]
