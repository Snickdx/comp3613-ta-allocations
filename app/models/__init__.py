"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.assignment import Assignment
from app.models.course import Course
from app.models.department import Department
from app.models.ta import Ta
from app.models.ta_experience import TaExperience
from app.models.user import User

__all__ = [
    "User",
    "Ta",
    "Course",
    "TaExperience",
    "Assignment",
    "Department",
]
