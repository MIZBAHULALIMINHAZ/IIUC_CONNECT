# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from accounts.serializers import (
    DepartmentListSerializer, RegisterSerializer, LoginSerializer, OTPVerifySerializer,
    ProfileUpdateSerializer, ProfileSerializer
)
from .models import User
from .utils import create_and_send_otp
from django.conf import settings
import jwt
import datetime
from cloudinary.uploader import upload as cloudinary_upload
from .models import User, Department
from accounts.serializers import DepartmentSerializer, UserActivationSerializer
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication
from cloudinary.exceptions import Error as CloudinaryError

def upload_image(file_obj, folder="iiuc_connect_profiles"):
    try:
        result = cloudinary_upload(file_obj, folder=folder, overwrite=True, resource_type="image")
        url = result.get("secure_url")
        if not url or not isinstance(url, str):
            raise Exception("Invalid URL returned from Cloudinary")
        return url
    except Exception as e:
        raise e

def delete_image(public_id):
    """Delete file from Cloudinary using public_id"""
    try:
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        if result.get("result") != "ok":
            raise Exception(f"Failed to delete image: {result}")
        return True
    except CloudinaryError as e:
        raise Exception(f"Cloudinary delete error: {str(e)}")
    
from urllib.parse import urlparse

def extract_public_id(url: str) -> str:
    """
    Extract Cloudinary public_id from secure URL
    Example:
    https://res.cloudinary.com/demo/image/upload/v1234567890/folder/myfile.jpg
    -> folder/myfile
    """
    path = urlparse(url).path  # /demo/image/upload/v1234567890/folder/myfile.jpg
    parts = path.split("/")
    # Last 2 parts are folder/file.extension
    public_id_with_ext = "/".join(parts[4:])  # folder/myfile.jpg
    public_id = ".".join(public_id_with_ext.split(".")[:-1])  # remove extension
    return public_id

# Register
class RegisterAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        # uniqueness checks
        if User.objects(student_id=data["student_id"]).first():
            return Response({"error": "student_id already exists"}, status=400)
        if User.objects(email=data["email"]).first():
            return Response({"error": "email already exists"}, status=400)
        email = data["email"]
        if email.endswith("@ugrad.iiuc.ac.bd"):
            is_active =  "yes"
        else:
            is_active = "no"
        user = User(
            student_id=data["student_id"],
            email=data["email"],
            name=data["name"],
            profile_picture="",  # default empty string
            is_active=is_active,
        )
        user.set_password(data["password"])

        # handle profile picture file -> upload to cloudinary and store URL
        if "profile_picture" in request.FILES:
            try:
                user.profile_picture = upload_image(request.FILES["profile_picture"])
            except Exception as e:
                return Response({"error": "Image upload failed", "detail": str(e)}, status=500)

        user.save()
        create_and_send_otp(user)
        return Response({"message": "User created. OTP sent to email."}, status=201)


# Login -> returns JWT if verified
class LoginAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        data = serializer.validated_data
        user = User.objects(email=data["email"]).first()
        if not user or not user.check_password(data["password"]):
            return Response({"error": "Invalid credentials"}, status=401)

        if user.is_verified != "yes":
            return Response({"error": "Email not verified. Please verify OTP."}, status=403)
        if user.is_active != "yes":
            return Response({"error": "Email is from outside. wait for admin activation."}, status=401)

        # Build JWT token
        payload = {
            "user_id": str(user.id),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
            "iat": datetime.datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        profile_data = ProfileSerializer({
            "id": str(user.id),
            "student_id": user.student_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "batch": user.batch,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified,
            "is_active": user.is_active
            
        }).data

        return Response({"token": token, "user": profile_data})


# Verify OTP
class VerifyOTPAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        if not user.otp or user.otp != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        # check expiry (10 minutes)
        if not user.otp_created_at:
            return Response({"error": "OTP timestamp missing"}, status=400)

        ttl = datetime.timedelta(minutes=10)
        if datetime.datetime.utcnow() > user.otp_created_at + ttl:
            return Response({"error": "OTP expired"}, status=400)

        # verified
        user.is_verified = "yes"
        user.otp = None
        user.otp_created_at = None
        user.save()
        return Response({"message": "Email verified successfully"})




# Profile view (GET/PUT) — uses JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import JWTAuthentication

class ProfileAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def get(self, request):
        user = request.user

        data = {
            "id": str(user.id),
            "student_id": user.student_id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "batch": user.batch,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified,
            "is_active": user.is_active
        }
        return Response(data)

    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        validated = serializer.validated_data
        for field in ["name", "department", "batch"]:
            if field in validated:
                setattr(user, field, validated[field])

        if "profile_picture" in request.FILES:
            try:
                user.profile_picture = upload_image(request.FILES["profile_picture"])
            except Exception as e:
                return Response({"error": "Image upload failed", "detail": str(e)}, status=500)

        user.save()
        return Response({"message": "Profile updated successfully"})
    
    



# Manager/Admin: Add Department
class DepartmentCreateAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def post(self, request):
        # Only admin/manager allowed
        if request.user.role not in ["admin", "teacher"]:
            return Response({"error": "Permission denied"}, status=403)

        serializer = DepartmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        if Department.objects(name=data["name"]).first() or Department.objects(code=data["code"]).first():
            return Response({"error": "Department already exists"}, status=400)

        dept = Department(
            name=data["name"],
            code=data["code"],
            is_active="yes"
        )
        dept.save()
        return Response({"message": "Department created successfully"}, status=201)


# Manager/Admin: List inactive users + activate
class InactiveUsersAPIView(APIView):
    authentication_classes = (JWTAuthentication,)

    def get(self, request):
        # Only admin allowed
        if request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        inactive_users = User.objects(is_active="no")
        serializer = UserActivationSerializer(inactive_users, many=True)
        return Response(serializer.data)

    def put(self, request):
        if request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        user_id = request.data.get("id")
        user = User.objects(id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        user.is_active = "yes"
        user.save()
        return Response({"message": "User activated successfully"})

# List active departments (all users can access)
class DepartmentListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        departments = Department.objects(is_active="yes")
        serializer = DepartmentListSerializer(departments, many=True)
        return Response(serializer.data)
