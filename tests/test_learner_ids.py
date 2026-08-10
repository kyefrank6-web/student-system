import uuid

from app import app, db
from auth_utils import hash_password
from learner_ids import assign_student_code, derive_school_initials, normalize_student_code
from models import School, Student, User


def test_derive_school_initials():
    assert derive_school_initials("St Kizito High School") == "KIZ"
    assert derive_school_initials("Greenhill Academy") == "GRE"
    assert len(derive_school_initials("Test")) == 3


def test_normalize_student_code():
    assert normalize_student_code("kiz001") == "KIZ-001"
    assert normalize_student_code("KIZ-001") == "KIZ-001"
    assert normalize_student_code("bad") is None


def test_assign_student_code_sequential():
    suffix = uuid.uuid4().hex[:8]
    with app.app_context():
        school = School(
            name="Lakeview Primary",
            status="approved",
            initials=derive_school_initials("Lakeview Primary"),
        )
        db.session.add(school)
        db.session.flush()
        teacher = User(
            name="Teacher",
            email=f"t-{suffix}@test.edu",
            password=hash_password("pass"),
            role="teacher",
            school_id=school.id,
            class_level="P1",
        )
        db.session.add(teacher)
        db.session.flush()

        first = Student(name="A", class_level="P1", school_id=school.id)
        second = Student(name="B", class_level="P1", school_id=school.id)
        db.session.add_all([first, second])
        db.session.flush()
        code1 = assign_student_code(first)
        code2 = assign_student_code(second)
        db.session.commit()

        assert code1.endswith("-001")
        assert code2.endswith("-002")
        assert code1[:3] == code2[:3]
