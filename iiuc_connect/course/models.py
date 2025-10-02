import mongoengine as me
from accounts.models import Department  # ধরে নিচ্ছি Department model আছে


class Course(me.Document):
    course_code = me.StringField(required=True, unique=True, max_length=20)  # Indexed unique
    department = me.ReferenceField(Department, reverse_delete_rule=me.CASCADE, required=True)  # FK relation
    credit_hour = me.IntField(required=True, min_value=0, max_value=5)

    # Cloudinary resource links (List of URLs)
    mid_theory_resources = me.ListField(me.URLField(), default=list)        # List of URLs
    mid_previous_solves = me.ListField(me.URLField(), default=list)
    final_resources = me.ListField(me.URLField(), default=list)
    final_previous_solves = me.ListField(me.URLField(), default=list)

    meta = {
        "collection": "courses",
        "indexes": [
            "course_code",
            "department",
        ],
        "ordering": ["course_code"],  # Default sort by course_code
    }

    def __str__(self):
        return f"{self.course_code} ({self.department.name})"
