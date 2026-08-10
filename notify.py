"""In-app notifications and optional email delivery."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app

from models import Notification, User, db

KIND_EXIT_REQUEST = "exit_request"
KIND_DEPARTURE = "departure"
KIND_RETURN = "return"
KIND_REQUEST_DECISION = "request_decision"
KIND_SCHOOL_PENDING = "school_pending"
KIND_GENERAL = "general"


def class_display(class_level, stream=None):
    if not class_level:
        return ""
    return f"{class_level} {stream}" if stream else class_level


def movement_kind_from_message(message: str) -> str:
    text = (message or "").lower()
    if "returned to school" in text:
        return KIND_RETURN
    if "released from school" in text:
        return KIND_DEPARTURE
    return KIND_GENERAL


def push_notification(user_id: int, message: str, *, kind: str | None = None) -> None:
    db.session.add(
        Notification(
            user_id=user_id,
            message=message[:500],
            kind=kind or KIND_GENERAL,
        )
    )


def notify_users(user_ids: list[int], message: str, *, kind: str | None = None) -> None:
    for uid in user_ids:
        push_notification(uid, message, kind=kind)


def notify_class_teacher(student, message_text: str, *, kind: str | None = None) -> None:
    if not student or not student.class_level or not student.school_id:
        return
    q = User.query.filter_by(
        role="teacher",
        school_id=student.school_id,
        class_level=student.class_level,
    )
    if student.stream:
        q = q.filter_by(stream=student.stream)
    resolved_kind = kind or movement_kind_from_message(message_text)
    notify_users([t.id for t in q.all()], message_text, kind=resolved_kind)


def notify_superadmins(
    message: str,
    *,
    email_subject: str | None = "CampusPass: school registration",
    kind: str = KIND_SCHOOL_PENDING,
) -> None:
    supers = User.query.filter_by(role="superadmin").all()
    for admin in supers:
        alert_user(admin, message, email_subject=email_subject, kind=kind)


def notify_school_admins(
    school_id: int,
    message: str,
    *,
    email_subject: str | None = "CampusPass: school alert",
    kind: str = KIND_EXIT_REQUEST,
) -> None:
    if not school_id:
        return
    admins = User.query.filter_by(role="admin", school_id=school_id).all()
    for admin in admins:
        alert_user(admin, message, email_subject=email_subject, kind=kind)


def notify_student_stakeholders(student, message: str) -> None:
    """Class teacher(s) and linked parent on gate in/out (legacy single message)."""
    if not student:
        return
    kind = movement_kind_from_message(message)
    notify_class_teacher(student, message, kind=kind)
    if student.parent_id:
        parent = User.query.get(student.parent_id)
        alert_user(
            parent,
            message,
            email_subject="CampusPass: learner movement update",
            kind=kind,
        )


def notify_gate_movement(
    student,
    *,
    signed_in: bool,
    time_label: str,
    reason: str | None = None,
    manual_note: str = "",
) -> None:
    """Notify class teacher and linked parent when a child signs in or out at the gate."""
    if not student:
        return
    cls = class_display(student.class_level, student.stream)
    staff_tag = f"{student.name} ({cls})" if cls else student.name
    extra = manual_note or ""
    if signed_in:
        kind = KIND_RETURN
        staff_msg = (
            f"{staff_tag} has returned to school at {time_label}{extra}."
        )
        parent_msg = (
            f"Your child {student.name} has signed in at school at {time_label}{extra}."
        )
        email_subject = f"CampusPass: {student.name} signed in"
    else:
        kind = KIND_DEPARTURE
        reason_part = f" Reason: {reason}" if reason else ""
        staff_msg = (
            f"{staff_tag} has been released from school at {time_label}{extra}.{reason_part}"
        )
        parent_msg = (
            f"Your child {student.name} has signed out from school at {time_label}.{reason_part}"
        )
        email_subject = f"CampusPass: {student.name} signed out"

    notify_class_teacher(student, staff_msg, kind=kind)
    if student.parent_id:
        parent = User.query.get(student.parent_id)
        if parent and parent.role == "parent":
            alert_user(
                parent,
                parent_msg,
                email_subject=email_subject,
                kind=kind,
            )


def maybe_send_email(user: User, subject: str, body: str) -> bool:
    cfg = current_app.config
    host = cfg.get("MAIL_SERVER")
    if not host or not user or not user.email:
        return False
    port = int(cfg.get("MAIL_PORT") or 587)
    use_tls = cfg.get("MAIL_USE_TLS", True)
    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    sender = cfg.get("MAIL_DEFAULT_SENDER") or username
    if not sender:
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = user.email
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        return True
    except Exception:
        current_app.logger.exception("Failed to send email to %s", user.email)
        return False


def alert_user(
    user: User | None,
    message: str,
    *,
    email_subject: str | None = None,
    kind: str | None = None,
) -> None:
    if not user:
        return
    push_notification(user.id, message, kind=kind or KIND_GENERAL)
    if email_subject:
        maybe_send_email(user, email_subject, message)


def alert_users(users: list[User], message: str, *, email_subject: str | None = None) -> None:
    for u in users:
        alert_user(u, message, email_subject=email_subject)
