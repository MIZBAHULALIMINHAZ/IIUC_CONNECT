from rest_framework import serializers
from .models import Course
from accounts.models import Department

class CourseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    course_code = serializers.CharField()
    department = serializers.CharField()  # Department id as string
    credit_hour = serializers.IntegerField()

    mid_theory_resources = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )
    mid_previous_solves = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )
    final_resources = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )
    final_previous_solves = serializers.ListField(
        child=serializers.URLField(), required=False, default=list
    )

    def create(self, validated_data):
        # convert department id string to Department object
        dept_id = validated_data.pop("department", None)
        department = Department.objects(id=dept_id).first() if dept_id else None
        course = Course(department=department, **validated_data)
        course.save()
        return course

    def update(self, instance, validated_data):
        dept_id = validated_data.pop("department", None)
        if dept_id:
            instance.department = Department.objects(id=dept_id).first()
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
