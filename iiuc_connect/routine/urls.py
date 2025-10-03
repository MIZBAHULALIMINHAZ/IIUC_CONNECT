from django.urls import path
from .views import RoutineViewSet

urlpatterns = [
    path("", RoutineViewSet.as_view({'get': 'list', 'post': 'create'}), name="routine-list-create"),
    path("<str:pk>/", RoutineViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="routine-detail"),
]
