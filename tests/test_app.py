import os
import tempfile
import uuid
from io import BytesIO

import pytest

# Minimal valid 1×1 PNG for upload tests
_MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x01"
    b"\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

from app import app, db
from auth_utils import hash_password, password_matches
from models import Notification, School, Student, User
from notify import KIND_EXIT_REQUEST, KIND_SCHOOL_PENDING, push_notification


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
            "RFID_API_KEY": "",
        }
    )
    with app.app_context():
        app.config["_app_init_done"] = False
        db.drop_all()
        db.create_all()
    with app.test_client() as c:
        yield c
    os.unlink(db_path)


def _seed_school_with_parent(client):
    suffix = uuid.uuid4().hex[:8]
    with app.app_context():
        school = School(name="Test School", status="approved")
        db.session.add(school)
        db.session.flush()
        admin = User(
            name="Admin",
            email=f"admin-{suffix}@test.edu",
            password=hash_password("adminpass"),
            role="admin",
            school_id=school.id,
        )
        parent = User(
            name="Parent One",
            email=f"parent-{suffix}@test.edu",
            password=hash_password("parentpass"),
            role="parent",
            school_id=school.id,
        )
        db.session.add_all([admin, parent])
        db.session.flush()
        child = Student(
            name="Child A",
            class_level="P3",
            school_id=school.id,
            parent_id=parent.id,
            rfid_tag="RFID-TEST-1",
        )
        db.session.add(child)
        db.session.commit()
        return {
            "school_id": school.id,
            "parent_email": parent.email,
            "admin_email": admin.email,
            "child_id": child.id,
        }


def test_register_school_notifies_superadmin(client):
    with app.app_context():
        if not User.query.filter_by(role="superadmin").first():
            db.session.add(
                User(
                    name="Super Admin",
                    email="superadmin@system.com",
                    password=hash_password("admin123"),
                    role="superadmin",
                    school_id=None,
                )
            )
            db.session.commit()

    suffix = uuid.uuid4().hex[:8]
    res = client.post(
        "/register_school",
        data={
            "school_name": f"Pending School {suffix}",
            "admin_name": "Campus Admin",
            "admin_email": f"pending-admin-{suffix}@test.edu",
            "admin_password": "securepass99",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    with app.app_context():
        superadmin = User.query.filter_by(role="superadmin").first()
        assert superadmin is not None
        note = (
            Notification.query.filter_by(
                user_id=superadmin.id, kind=KIND_SCHOOL_PENDING
            )
            .order_by(Notification.id.desc())
            .first()
        )
        assert note is not None
        assert "Pending School" in note.message
        assert "awaits approval" in note.message.lower()


def test_teacher_can_download_parent_import_logins(client):
    data = _seed_teacher_with_class(client)
    with client.session_transaction() as sess:
        sess["parent_import_logins"] = [
            {
                "name": "Guardian A",
                "email": "guardian-a@test.edu",
                "password": "temp-pass-1",
            }
        ]

    client.post("/login", data={"email": data["teacher_email"], "password": "teacherpass"})
    res = client.get("/students/import/parent-logins")
    assert res.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in res.content_type
    )
    assert b"PK" in res.data[:4]


def test_password_hashing():
    h = hash_password("secret")
    assert password_matches(h, "secret")
    assert not password_matches(h, "wrong")


def test_parent_can_access_requests(client):
    data = _seed_school_with_parent(client)
    client.post("/login", data={"email": data["parent_email"], "password": "parentpass"})
    res = client.get("/requests")
    assert res.status_code == 200
    assert b"New request" in res.data


def _seed_school_with_nurse(client):
    suffix = uuid.uuid4().hex[:8]
    with app.app_context():
        school = School(name="Nurse Test School", status="approved")
        db.session.add(school)
        db.session.flush()
        nurse = User(
            name="School Nurse",
            email=f"nurse-{suffix}@test.edu",
            password=hash_password("nursepass"),
            role="nurse",
            school_id=school.id,
        )
        db.session.add(nurse)
        db.session.flush()
        alpha = Student(name="Alpha Learner", class_level="P1", school_id=school.id)
        beta = Student(name="Beta Learner", class_level="S2", school_id=school.id)
        db.session.add_all([alpha, beta])
        db.session.commit()
        return {
            "nurse_email": nurse.email,
            "alpha_id": alpha.id,
        }


def test_nurse_requests_uses_student_search_picker(client):
    data = _seed_school_with_nurse(client)
    client.post("/login", data={"email": data["nurse_email"], "password": "nursepass"})
    res = client.get("/requests")
    assert res.status_code == 200
    assert b"data-student-picker" in res.data
    assert b"Search by name, class, or RFID" in res.data
    assert b'student-picker.js' in res.data
    assert b'<select id="student_id"' not in res.data


def test_nurse_can_create_request_with_picker(client):
    data = _seed_school_with_nurse(client)
    client.post("/login", data={"email": data["nurse_email"], "password": "nursepass"})
    res = client.post(
        "/create_request",
        data={"student_id": data["alpha_id"], "reason": "Clinic visit"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"submitted" in res.data.lower()


def test_parent_cannot_request_unlinked_child(client):
    data = _seed_school_with_parent(client)
    with app.app_context():
        other = Student(
            name="Stranger",
            class_level="P4",
            school_id=data["school_id"],
        )
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    client.post("/login", data={"email": data["parent_email"], "password": "parentpass"})
    res = client.post(
        "/create_request",
        data={"student_id": other_id, "reason": "Test"},
        follow_redirects=True,
    )
    assert b"own children" in res.data


def _seed_teacher_with_class(client):
    suffix = uuid.uuid4().hex[:8]
    with app.app_context():
        school = School(name="Photo School", status="approved")
        db.session.add(school)
        db.session.flush()
        teacher = User(
            name="Class Teacher",
            email=f"teacher-photo-{suffix}@test.edu",
            password=hash_password("teacherpass"),
            role="teacher",
            school_id=school.id,
            class_level="P2",
        )
        db.session.add(teacher)
        db.session.commit()
        return {"teacher_email": teacher.email, "school_id": school.id}


def test_teacher_can_add_learner_profile_photo(client):
    data = _seed_teacher_with_class(client)
    client.post("/login", data={"email": data["teacher_email"], "password": "teacherpass"})
    res = client.post(
        "/students/register",
        data={
            "name": "Photo Learner",
            "class_level": "P2",
            "stream": "",
            "photo": (BytesIO(_MINI_PNG), "learner.png"),
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"was added" in res.data

    with app.app_context():
        learner = Student.query.filter_by(name="Photo Learner").first()
        assert learner is not None
        assert learner.photo_filename
        assert learner.photo_filename.endswith(".png")
        photo_name = learner.photo_filename

    photo_res = client.get(f"/student-photos/{photo_name}")
    assert photo_res.status_code == 200
    assert photo_res.mimetype.startswith("image/")


def test_register_student_creates_parent(client):
    suffix = uuid.uuid4().hex[:8]
    with app.app_context():
        school = School(name="Auto Parent School", status="approved")
        db.session.add(school)
        db.session.flush()
        teacher = User(
            name="Teacher",
            email=f"teacher-auto-{suffix}@test.edu",
            password=hash_password("teacherpass"),
            role="teacher",
            school_id=school.id,
            class_level="P2",
        )
        db.session.add(teacher)
        db.session.commit()
        teacher_email = teacher.email
        school_id = school.id

    client.post("/login", data={"email": teacher_email, "password": "teacherpass"})
    parent_email = f"guardian-{suffix}@test.edu"
    res = client.post(
        "/students/register",
        data={
            "name": "New Learner",
            "class_level": "P2",
            "parent_name": "Guardian Name",
            "parent_email": parent_email,
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Parent portal login created" in res.data
    assert parent_email.encode() in res.data

    with app.app_context():
        parent = User.query.filter_by(email=parent_email, role="parent").first()
        assert parent is not None
        assert parent.school_id == school_id
        learner = Student.query.filter_by(name="New Learner").first()
        assert learner is not None
        assert learner.parent_id == parent.id


def test_poll_notifications_admin(client):
    data = _seed_school_with_parent(client)
    with app.app_context():
        admin = User.query.filter_by(email=data["admin_email"]).first()
        push_notification(
            admin.id,
            "New exit request for Child A (P3): Medical.",
            kind=KIND_EXIT_REQUEST,
        )
        db.session.commit()
        notif_id = (
            Notification.query.filter_by(user_id=admin.id)
            .order_by(Notification.id.desc())
            .first()
            .id
        )

    client.post("/login", data={"email": data["admin_email"], "password": "adminpass"})
    res = client.get(f"/api/notifications/poll?since_id={notif_id - 1}")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["notifications"]) == 1
    assert body["notifications"][0]["kind"] == "exit_request"


def test_change_password(client):
    data = _seed_school_with_parent(client)
    with app.app_context():
        admin = User.query.filter_by(email=data["admin_email"]).first()
        admin.password = hash_password("oldpass12")
        db.session.commit()

    client.post("/login", data={"email": data["admin_email"], "password": "oldpass12"})
    res = client.post(
        "/account/password",
        data={
            "current_password": "oldpass12",
            "new_password": "newpass99",
            "confirm_password": "newpass99",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"password was updated" in res.data

    client.get("/logout")
    ok = client.post(
        "/login",
        data={"email": data["admin_email"], "password": "newpass99"},
        follow_redirects=True,
    )
    assert ok.status_code == 200
    assert b"Wrong password" not in ok.data


def test_parent_notified_on_gate_movement(client):
    from models import Notification, Request
    from notify import KIND_DEPARTURE, KIND_RETURN

    data = _seed_school_with_parent(client)
    with app.app_context():
        req = Request(
            student_id=data["child_id"],
            requested_by=1,
            reason="Medical",
            status="approved",
        )
        db.session.add(req)
        db.session.commit()
        parent = User.query.filter_by(email=data["parent_email"]).first()
        parent_id = parent.id

    client.post("/rfid_scan", json={"rfid": "RFID-TEST-1"})
    client.post("/rfid_scan", json={"rfid": "RFID-TEST-1"})

    with app.app_context():
        kinds = [
            n.kind
            for n in Notification.query.filter_by(user_id=parent_id).all()
        ]
        assert KIND_DEPARTURE in kinds
        assert KIND_RETURN in kinds
        out_msg = (
            Notification.query.filter_by(user_id=parent_id, kind=KIND_DEPARTURE)
            .first()
            .message
        )
        assert "Your child" in out_msg
        assert "signed out" in out_msg.lower()


def test_poll_notifications_parent_movement(client):
    from models import Notification
    from notify import KIND_RETURN, push_notification

    data = _seed_school_with_parent(client)
    with app.app_context():
        parent = User.query.filter_by(email=data["parent_email"]).first()
        push_notification(
            parent.id,
            "Your child Child A has signed in at school at 14:00.",
            kind=KIND_RETURN,
        )
        db.session.commit()
        notif_id = (
            Notification.query.filter_by(user_id=parent.id)
            .order_by(Notification.id.desc())
            .first()
            .id
        )

    client.post("/login", data={"email": data["parent_email"], "password": "parentpass"})
    res = client.get(f"/api/notifications/poll?since_id={notif_id - 1}")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["notifications"]) == 1
    assert body["notifications"][0]["kind"] == "return"


def test_rfid_scan_sign_out_and_in(client):
    data = _seed_school_with_parent(client)
    with app.app_context():
        from models import Request

        req = Request(
            student_id=data["child_id"],
            requested_by=1,
            reason="Medical",
            status="approved",
        )
        db.session.add(req)
        db.session.commit()

    res = client.post("/rfid_scan", json={"rfid": "RFID-TEST-1"})
    assert res.status_code == 200
    assert res.get_json()["message"] == "Student signed OUT"

    res2 = client.post("/rfid_scan", json={"rfid": "RFID-TEST-1"})
    assert res2.status_code == 200
    assert res2.get_json()["message"] == "Student signed IN"

    with app.app_context():
        req = Request.query.filter_by(student_id=data["child_id"]).first()
        assert req is not None
        assert req.status == "completed"

    res3 = client.post("/rfid_scan", json={"rfid": "RFID-TEST-1"})
    assert res3.status_code == 403
    body3 = res3.get_json()
    assert "approved" in body3["error"].lower()
    assert body3.get("student", {}).get("name") == "Child A"
