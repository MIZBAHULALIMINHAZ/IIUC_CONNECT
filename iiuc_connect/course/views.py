from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Course
from .serializers import CourseSerializer
from accounts.models import Department
from accounts.views import upload_image, delete_image, extract_public_id
from accounts.authentication import JWTAuthentication

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    authentication_classes = (JWTAuthentication,)

    def is_admin(self, user):
        return getattr(user, "role", None) in ["admin", "teacher"]

    def create(self, request, *args, **kwargs):
        course_code = request.data.get("course_code")
        if Course.objects(course_code=course_code).first():
            return Response({"error": "Course code already exists"}, status=400)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def add_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        course = self.get_object()
        file_obj = request.FILES.get("file")
        field_name = request.data.get("field")

        if not file_obj or not field_name:
            return Response({"error": "File and field are required"}, status=400)
        if not hasattr(course, field_name):
            return Response({"error": "Invalid resource field"}, status=400)

        url = upload_image(file_obj, folder="iiuc_connect_courses")
        getattr(course, field_name).append(url)
        course.save()
        return Response({"message": "Resource added", "url": url})

    @action(detail=True, methods=["put"])
    def update_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        course = self.get_object()
        field_name = request.data.get("field")
        old_url = request.data.get("old_url")
        file_obj = request.FILES.get("file")

        if not all([file_obj, field_name, old_url]):
            return Response({"error": "file, field and old_url required"}, status=400)
        if not hasattr(course, field_name):
            return Response({"error": "Invalid field"}, status=400)

        resources = getattr(course, field_name)
        if old_url not in resources:
            return Response({"error": "old_url not found in resources"}, status=400)

        delete_image(extract_public_id(old_url))
        new_url = upload_image(file_obj, folder="iiuc_connect_courses")
        resources[resources.index(old_url)] = new_url
        setattr(course, field_name, resources)
        course.save()
        return Response({"message": "Resource updated", "url": new_url})

    @action(detail=True, methods=["delete"])
    def delete_resource(self, request, pk=None):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        course = self.get_object()
        field_name = request.data.get("field")
        target_url = request.data.get("url")

        if not all([field_name, target_url]):
            return Response({"error": "field and url required"}, status=400)
        if not hasattr(course, field_name):
            return Response({"error": "Invalid field"}, status=400)

        resources = getattr(course, field_name)
        if target_url not in resources:
            return Response({"error": "URL not found in resources"}, status=400)

        delete_image(extract_public_id(target_url))
        resources.remove(target_url)
        setattr(course, field_name, resources)
        course.save()
        return Response({"message": "Resource deleted"})


class CourseResourcesAPIView(APIView):
    """
    Logged-in users can view courses and their resources (read-only).
    """
    authentication_classes = (JWTAuthentication,)

    def get(self, request):
        courses = Course.objects.all()
        data = []
        for course in courses:
            data.append({
                "id": str(course.id),
                "course_code": course.course_code,
                "department": str(course.department.name) if course.department else None,
                "credit_hour": course.credit_hour,
                "mid_theory_resources": course.mid_theory_resources,
                "mid_previous_solves": course.mid_previous_solves,
                "final_resources": course.final_resources,
                "final_previous_solves": course.final_previous_solves
            })
        return Response({"courses": data})
