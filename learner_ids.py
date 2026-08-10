"""School-scoped learner display IDs (e.g. SKT-001)."""

from __future__ import annotations

import re

from sqlalchemy import func

from models import School, Student, db

_SKIP_WORDS = frozenset(
    {
        "the",
        "of",
        "and",
        "a",
        "an",
        "st",
        "st.",
        "saint",
        "school",
        "high",
        "primary",
        "secondary",
        "college",
        "academy",
        "international",
        "junior",
        "senior",
        "preparatory",
        "prep",
    }
)

_CODE_RE = re.compile(r"^([A-Za-z]{2,4})-(\d{3})$")


def derive_school_initials(school_name: str) -> str:
    """Up to 3 letters from the school name (e.g. 'St Kizito High' -> SKH)."""
    words = re.findall(r"[A-Za-z0-9]+", school_name or "")
    significant = [w for w in words if w.lower() not in _SKIP_WORDS]
    if not significant:
        significant = words
    if not significant:
        return "SCH"
    if len(significant) == 1:
        return significant[0][:3].upper().ljust(3, "X")[:3]
    letters = "".join(w[0].upper() for w in significant)
    if len(letters) >= 3:
        return letters[:3]
    return (letters + significant[0][1:]).upper().ljust(3, "X")[:3]


def normalize_student_code(raw: str) -> str | None:
    """Accept SKT-001, SKT001, skt 001 -> SKT-001."""
    text = (raw or "").strip().upper().replace(" ", "")
    if not text:
        return None
    m = re.match(r"^([A-Z]{2,4})-?(\d{3})$", text)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def display_student_id(student) -> str:
    code = getattr(student, "student_code", None) if student else None
    if code:
        return code
    if student and getattr(student, "id", None):
        return f"#{student.id}"
    return ""


def _max_sequence_for_school(school_id: int, initials: str) -> int:
    prefix = initials.upper()
    pattern = f"{prefix}-"
    max_n = 0
    rows = (
        db.session.query(Student.student_code)
        .filter_by(school_id=school_id)
        .filter(Student.student_code.isnot(None))
        .all()
    )
    for (code,) in rows:
        if not code:
            continue
        m = _CODE_RE.match(code.strip().upper())
        if m and m.group(1) == prefix:
            max_n = max(max_n, int(m.group(2)))
    return max_n


def next_student_code(school: School) -> str:
    initials = (school.initials or derive_school_initials(school.name or "")).upper()
    if not school.initials:
        school.initials = initials
    seq = _max_sequence_for_school(school.id, initials) + 1
    if seq > 999:
        raise ValueError(
            f"Learner ID limit reached for {initials} (999 learners). Contact support."
        )
    return f"{initials}-{seq:03d}"


def assign_student_code(learner: Student) -> str:
    if learner.student_code:
        return learner.student_code
    school = School.query.get(learner.school_id)
    if not school:
        return ""
    code = next_student_code(school)
    learner.student_code = code
    return code


def backfill_all_student_codes() -> None:
    for school in School.query.all():
        if not school.initials:
            school.initials = derive_school_initials(school.name or "School")
        initials = school.initials.upper()
        students = (
            Student.query.filter_by(school_id=school.id)
            .order_by(Student.id.asc())
            .all()
        )
        seq = 0
        for student in students:
            if student.student_code:
                m = _CODE_RE.match(student.student_code.strip().upper())
                if m and m.group(1) == initials:
                    seq = max(seq, int(m.group(2)))
                continue
            seq += 1
            if seq > 999:
                break
            student.student_code = f"{initials}-{seq:03d}"
    db.session.commit()


def find_student_by_lookup(query: str, *, school_id: int | None = None):
    """Resolve learner by display ID, legacy numeric id, RFID, or name."""
    q = (query or "").strip()
    if not q:
        return None

    student = None
    normalized = normalize_student_code(q)
    if normalized:
        base = Student.query.filter(
            func.upper(Student.student_code) == normalized.upper()
        )
        if school_id:
            base = base.filter_by(school_id=school_id)
        student = base.first()

    if not student and q.isdigit():
        base = Student.query.filter_by(id=int(q))
        if school_id:
            base = base.filter_by(school_id=school_id)
        student = base.first()

    if not student:
        base = Student.query.filter_by(rfid_tag=q)
        if school_id:
            base = base.filter_by(school_id=school_id)
        student = base.first()

    if not student:
        base = Student.query.filter(func.lower(Student.name).contains(q.lower()))
        if school_id:
            base = base.filter_by(school_id=school_id)
        student = base.first()

    return student
