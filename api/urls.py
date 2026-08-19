from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    CategoryViewSet,
    ClubViewSet,
    CoachViewSet,
    ContestViewSet,
    EntryViewSet,
    ResultViewSet,
    SwimmerViewSet,
    SwimstyleViewSet,
)

app_name = 'api'

v1_router = DefaultRouter()
v1_router.register('coaches', CoachViewSet, basename='coaches')
v1_router.register('swimmers', SwimmerViewSet, basename='swimmers')
v1_router.register('categories', CategoryViewSet, basename='categories')
v1_router.register('swim_styles', SwimstyleViewSet, basename='styles')
v1_router.register('clubs', ClubViewSet, basename='clubs')
v1_router.register('contests', ContestViewSet, basename='contests')
v1_router.register('entries', EntryViewSet, basename='entries')
v1_router.register('results', ResultViewSet, basename='results')


urlpatterns = [
    path('v1/', include(v1_router.urls)),
]
