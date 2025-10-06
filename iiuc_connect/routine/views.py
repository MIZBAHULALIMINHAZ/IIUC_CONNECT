# routine/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from mongoengine.queryset.visitor import Q
from .models import Routine
from .serializers import RoutineSerializer
from course.models import CourseRegistration
from accounts.authentication import JWTAuthentication

class RoutineViewSet(viewsets.ModelViewSet):
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
            # Student: fetch registered courses & sections
            regs = CourseRegistration.objects(student=user, status="confirmed")
            query = Q()
            for r in regs:
                query |= Q(course=r.course, section=r.section)
            return Routine.objects(query)

    def create(self, request, *args, **kwargs):
        if not self.is_admin(request.user):
            return Response({"error": "Permission denied"}, status=403)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()

        # Teacher auto-registration
        reg = CourseRegistration.objects(
            student=routine.teacher,
            course=routine.course,
            section=routine.section
        ).first()
        if reg:
            reg.status = "confirmed"
            reg.save()
        else:
            CourseRegistration(
                student=routine.teacher,
                course=routine.course,
                section=routine.section,
                status="confirmed"
            ).save()

        return Response(
            {"message": "Routine created & teacher registered", "routine": serializer.data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        routine = self.get_object()
        serializer = self.get_serializer(routine, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        routine = serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        routine = self.get_object()
        routine.delete()
        return Response({"message": "Routine deleted"}, status=status.HTTP_200_OK)
