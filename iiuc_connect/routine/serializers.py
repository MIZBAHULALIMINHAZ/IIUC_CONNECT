# routine/serializers.py
from rest_framework import serializers
from .models import Routine
from course.models import CourseRegistration, Course
from accounts.models import User, Department
import mongoengine as me

class RoutineSerializer(serializers.Serializer):
    course = serializers.CharField()
    teacher = serializers.CharField()
    department = serializers.CharField()
    day = serializers.CharField()
    period = serializers.IntegerField(min_value=1, max_value=6)
    room_number = serializers.CharField()
    section = serializers.CharField()

    def validate(self, data):
        # Convert IDs to objects
        course = Course.objects(id=data["course"]).first()
        teacher = User.objects(id=data["teacher"]).first()
        department = Department.objects(id=data["department"]).first()

        if not course:
            raise serializers.ValidationError("Invalid course ID")
        if not teacher:
            raise serializers.ValidationError("Invalid teacher ID")
        if not department:
            raise serializers.ValidationError("Invalid department ID")

        day = data["day"]
        period = data["period"]
        section = data["section"]
        room = data["room_number"]

        # Teacher conflict
        if Routine.objects(teacher=teacher, day=day, period=period, section=section).first():
            raise serializers.ValidationError("Teacher already has a routine at this time")

        # Room conflict
        if Routine.objects(room_number=room, day=day, period=period).first():
            raise serializers.ValidationError("Room already occupied at this time")

        # Course-section conflict
        if Routine.objects(course=course, day=day, period=period, section=section).first():
            raise serializers.ValidationError("Course already scheduled at this time for this section")

        # Attach objects for create/update
        data["course"] = course
        data["teacher"] = teacher
        data["department"] = department
        return data

    def create(self, validated_data):
        routine = Routine(**validated_data)
        routine.save()
        return routine

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "course": {
                "id": str(instance.course.id),
                "code": instance.course.course_code
            },
            "teacher": {
                "id": str(instance.teacher.id),
                "name": instance.teacher.name
            },
            "department": {
                "id": str(instance.department.id),
                "name": instance.department.name
            },
            "day": instance.day,
            "period": instance.period,
            "room_number": instance.room_number,
            "section": instance.section
        }
