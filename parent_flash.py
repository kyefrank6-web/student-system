"""Flash messages for newly created parent credentials."""

from __future__ import annotations

import html

from markupsafe import Markup
from flask import flash


def flash_new_parent_credentials(credentials: list[tuple[str, str, str]]) -> None:
    """Each item is (parent_name, email, plain_password)."""
    if not credentials:
        return
    parts = []
    for pname, email, password in credentials:
        parts.append(
            f"<strong>{html.escape(pname)}</strong> — "
            f"email: <code>{html.escape(email)}</code> · "
            f"password: <code>{html.escape(password)}</code>"
        )
    flash(
        Markup(
            "<strong>Parent portal login created</strong> (share securely with the family):<br/>"
            + "<br/>".join(parts)
        ),
        "info",
    )
