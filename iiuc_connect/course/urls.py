from django.urls import path
from course.views import CourseResourcesAPIView, CourseViewSet

urlpatterns = [
    path("", CourseViewSet.as_view({'get': 'list', 'post': 'create'}), name="course-list-create"),
    path("one/<str:pk>/", CourseViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="course-detail"),
    path("<str:pk>/add_resource/", CourseViewSet.as_view({'post': 'add_resource'}), name="course-add-resource"),
    path("<str:pk>/update_resource/", CourseViewSet.as_view({'put': 'update_resource'}), name="course-update-resource"),
    path("<str:pk>/delete_resource/", CourseViewSet.as_view({'delete': 'delete_resource'}), name="course-delete-resource"),
    path("allcheck/", CourseResourcesAPIView.as_view(), name="course-resources"),
]
