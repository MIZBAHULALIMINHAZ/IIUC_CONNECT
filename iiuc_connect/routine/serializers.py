from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from .models import Routine
from course.models import CourseRegistration, Course
from accounts.models import User, Department

class RoutineSerializer(serializers.Serializer):
    course = serializers.CharField()
    teacher = serializers.CharField()
    department = serializers.CharField()
    day = serializers.CharField()
    period = serializers.IntegerField()
    room_number = serializers.CharField()
    section = serializers.CharField()

    def create(self, validated_data):
        validated_data["course"] = Course.objects(id=validated_data["course"]).first()
        validated_data["teacher"] = User.objects(id=validated_data["teacher"]).first()
        validated_data["department"] = Department.objects(id=validated_data["department"]).first()
        routine = Routine(**validated_data)
        routine.save()
        return routine

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            if key == "course":
                value = Course.objects(id=value).first()
            elif key == "teacher":
                value = User.objects(id=value).first()
            elif key == "department":
                value = Department.objects(id=value).first()
            setattr(instance, key, value)
        instance.save()
        return instance

