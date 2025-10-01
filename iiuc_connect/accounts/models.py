# accounts/models.py
from mongoengine import Document, StringField, EmailField, DateTimeField
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    student_id = StringField(required=True, unique=True)       # unique, indexed
    email = EmailField(required=True, unique=True)             # unique, indexed
    name = StringField(required=True)
    password_hash = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    otp = StringField()               # for email verification or password reset
    otp_created_at = DateTimeField()  # timestamp for OTP validity
    is_verified = StringField(choices=['yes','no'], default='no') 
    is_active = StringField(choices=['yes','no'], default='no') # email verified
    role = StringField(choices=['student', 'admin', 'teacher'], default='student')
    department = StringField()       # optional
    batch = StringField()            # optional
    profile_picture = StringField()  # URL (Cloudinary)

    meta = {
        'collection': 'users',
        'indexes': ['student_id', 'email', 'role']
    }

    # Password setter
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    # Password checker
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Department(Document):
    name = StringField(required=True, unique=True)
    code = StringField(required=True, unique=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    is_active = StringField(choices=['yes', 'no'], default='yes')
    meta = {
        'collection': 'departments',
        'indexes': ['name', 'code']
    }