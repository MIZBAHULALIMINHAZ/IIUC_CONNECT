from course.models import Course, CourseRegistration
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Routine
from .serializers import RoutineSerializer
from accounts.authentication import JWTAuthentication

class RoutineViewSet(viewsets.ModelViewSet):
    queryset = Routine.objects.all()
    serializer_class = RoutineSerializer
    authentication_classes = (JWTAuthentication,)

    def is_admin(self, user):
        return getattr(user, "role", None) == "admin"

    def is_teacher(self, user):
        return getattr(user, "role", None) == "teacher"

    def get_queryset(self):
        user = self.request.user
        if self.is_admin(user):
            return Routine.objects.all()
        elif self.is_teacher(user):
            return Routine.objects(teacher=user)
        else:
            regs = CourseRegistration.objects(student=user, status="confirmed")
            return Routine.objects(course__in=[r.course for r in regs], section__in=[r.section for r in regs])

    def create(self, request, *args, **kwargs):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()

        # Teacher auto-registration
        reg = CourseRegistration.objects(student=routine.teacher, course=routine.course, section=routine.section).first()
        if reg:
            reg.status = "confirmed"
            reg.save()
        else:
            CourseRegistration(student=routine.teacher, course=routine.course, section=routine.section, status="confirmed").save()

        return Response({"message": "Routine created & teacher registered", "routine": serializer.data}, status=status.HTTP_201_CREATED)
