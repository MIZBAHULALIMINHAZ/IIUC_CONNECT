# accounts/utils.py
import jwt
import datetime
from django.conf import settings
from accounts.models import User

def generate_jwt(user_id):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),  # 1-day expiry
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def decode_jwt(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects(id=payload["user_id"]).first()
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# If you've configured cloudinary in settings, this is optional.
# import cloudinary
# import cloudinary.uploader
# from django.conf import settings

# cloudinary.config(
#     cloud_name=settings.CLOUD_NAME,
#     api_key=settings.CLOUD_API_KEY,
#     api_secret=settings.CLOUD_API_SECRET,
#     secure=True
# )


# def upload_image_to_cloudinary(file_obj, folder="iiuc_connect_profiles"):
#     """
#     Accepts Django InMemoryUploadedFile or FileStorage file object.
#     Returns secure_url string on success, raises Exception on failure.
#     """
#     try:
#         result = cloudinary.uploader.upload(file_obj, folder=folder, overwrite=True, resource_type="image")
#         return result.get("secure_url")
#     except Exception as e:
#         raise e
    
    # utils/otp_helper.py
import random
import datetime
from django.core.mail import send_mail
from django.conf import settings

OTP_TTL_MINUTES = 10

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_via_email(email, otp):
    subject = "Your IIUC Connect OTP"
    message = f"Your OTP code is {otp}. It is valid for {OTP_TTL_MINUTES} minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [email], fail_silently=False)
    
# accounts/utils.py
import datetime
from accounts.models import User

def create_and_send_otp(user):
    otp = generate_otp()
    user.otp = otp
    user.otp_created_at = datetime.datetime.utcnow()
    user.is_verified = "no"
    user.save()
    send_otp_via_email(user.email, otp)
