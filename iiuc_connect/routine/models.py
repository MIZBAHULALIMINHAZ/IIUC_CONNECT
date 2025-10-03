import mongoengine as me
from accounts.models import Department, User
from course.models import Course

class Routine(me.Document):
    course = me.ReferenceField(Course, required=True)
    teacher = me.ReferenceField(User, required=True)
    room_number = me.StringField(required=True)
    period = me.IntField(min_value=1, max_value=6, required=True)
    day = me.StringField(choices=["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday"], required=True)
    department = me.ReferenceField(Department, required=True)
    section = me.StringField(required=True)

    meta = {
        "collection": "routines",
        "indexes": ["course", "teacher", "day", "period", "department", "section"],
        "ordering": ["day", "period"]
    }

    def __str__(self):
        return f"{self.course.course_code} | {self.teacher.name} | {self.day} P{self.period}"
