"""Password hashing and verification (supports legacy plain-text rows)."""

from werkzeug.security import check_password_hash, generate_password_hash

MIN_PASSWORD_LENGTH = 8


def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def _is_hashed(stored: str) -> bool:
    return stored.startswith("pbkdf2:") or stored.startswith("scrypt:")


def password_matches(stored: str | None, plain: str) -> bool:
    stored = stored or ""
    if _is_hashed(stored):
        return check_password_hash(stored, plain)
    return stored == plain


def upgrade_password_if_needed(user, plain: str) -> bool:
    """Re-hash legacy plain passwords after successful login."""
    stored = user.password or ""
    if _is_hashed(stored):
        return False
    user.password = hash_password(plain)
    return True
