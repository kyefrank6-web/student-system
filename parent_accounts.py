"""Create or link parent accounts when learners are registered."""

from __future__ import annotations

import re
import secrets
import string

from sqlalchemy import func

from auth_utils import hash_password
from models import User, db

_PASSWORD_ALPHABET = "".join(
    c for c in (string.ascii_letters + string.digits) if c not in "0O1lI"
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def generate_parent_password(length: int = 10) -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))


def resolve_or_create_parent(
    school_id: int,
    *,
    name: str = "",
    email: str = "",
) -> tuple[User | None, str | None, str | None]:
    """
    Find an existing parent at this school or create one with a generated password.

    Returns (user, plain_password_if_new, error_message).
    """
    email = (email or "").strip().lower()
    if not email:
        return None, None, None

    if not _EMAIL_RE.match(email):
        return None, None, "Parent email address is not valid."

    existing = User.query.filter(func.lower(User.email) == email).first()
    if existing:
        if existing.role == "parent" and existing.school_id == school_id:
            if name.strip() and existing.name != name.strip():
                existing.name = name.strip()[:100]
            return existing, None, None
        return None, None, f"The email {email!r} is already used by another account."

    display_name = (name or "").strip() or f"Parent ({email.split('@')[0]})"
    plain = generate_parent_password()
    user = User(
        name=display_name[:100],
        email=email,
        password=hash_password(plain),
        role="parent",
        school_id=school_id,
    )
    db.session.add(user)
    db.session.flush()
    return user, plain, None
