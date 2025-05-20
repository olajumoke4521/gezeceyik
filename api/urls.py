from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'languages', views.LanguageViewSet, basename='language')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'places', views.PlaceViewSet, basename='place')


urlpatterns = [
    path('', include(router.urls)),
    path('filter-options/', views.FilterOptionsView.as_view(), name='filter-options'),
    path('wheel-spin/', views.WheelSpinView.as_view(), name='wheel-spin'),
]
