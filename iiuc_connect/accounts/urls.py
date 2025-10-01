# accounts/urls.py
# accounts/urls.py
from django.urls import path
from accounts.views import DepartmentCreateAPIView, DepartmentListAPIView, InactiveUsersAPIView, RegisterAPIView, LoginAPIView, VerifyOTPAPIView, ProfileAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPAPIView.as_view(), name="verify-otp"),
    path("me/", ProfileAPIView.as_view(), name="profile"),  # JWT-required
    
    path("departments/add/", DepartmentCreateAPIView.as_view(), name="add-department"),
    path("departments/", DepartmentListAPIView.as_view(), name="list-departments"),

    # User management APIs
    path("users/inactive/", InactiveUsersAPIView.as_view(), name="inactive-users"),
]
