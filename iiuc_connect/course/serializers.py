from rest_framework import serializers
from .models import Course, CourseRegistration, Payment
from accounts.models import Department, User

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id", "course_code", "department", "credit_hour",
            "mid_theory_resources", "mid_previous_solves",
            "final_resources", "final_previous_solves"
        ]

    def create(self, validated_data):
        dept = validated_data.pop("department", None)
        if isinstance(dept, str):
            dept = Department.objects(id=dept).first()
        course = Course(department=dept, **validated_data)
        course.save()
        return course

    def update(self, instance, validated_data):
        dept = validated_data.pop("department", None)
        if dept:
            if isinstance(dept, str):
                dept = Department.objects(id=dept).first()
            instance.department = dept
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

from rest_framework import serializers
from .models import CourseRegistration, Course, Payment
from accounts.models import User

class CourseRegistrationSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    section = serializers.CharField()
    status = serializers.CharField(read_only=True)

    def get_id(self, obj):
        return str(obj.id)

    def get_student(self, obj):
        return str(obj.student.id)

    def get_course(self, obj):
        return str(obj.course.id)

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context missing")

        student_id = validated_data.get('student') or request.data.get('student')
        course_id = validated_data.get('course') or request.data.get('course')
        section = validated_data.get('section')

        student = User.objects(id=student_id).first()
        course = Course.objects(id=course_id).first()

        if not student or not course:
            raise serializers.ValidationError("Invalid student or course")

        # Prevent duplicate registration
        existing = CourseRegistration.objects(student=student, course=course, section=section).first()
        if existing:
            return existing

        reg = CourseRegistration(student=student, course=course, section=section, status="pending")
        reg.save()
        return reg



from rest_framework import serializers
from .models import Payment, CourseRegistration

class PaymentSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    registration = serializers.CharField()
    amount = serializers.FloatField()
    method = serializers.CharField()
    status = serializers.CharField(read_only=True)
    transaction_id = serializers.CharField()

    def get_id(self, obj):
        return str(obj.id)

    def create(self, validated_data):
        registration_id = validated_data.get('registration')
        reg = CourseRegistration.objects(id=registration_id).first()
        if not reg:
            raise serializers.ValidationError("Invalid registration")

        payment = Payment(
            registration=reg,
            amount=validated_data.get('amount'),
            method=validated_data.get('method'),
            transaction_id=validated_data.get('transaction_id'),
            status="completed"
        )
        payment.save()

        # Update registration status
        reg.status = "confirmed"
        reg.save()

        return payment

