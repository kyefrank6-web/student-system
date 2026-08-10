from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class School(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    initials = db.Column(db.String(3), nullable=True)
    status = db.Column(db.String(20), default='pending')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50))
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    # Teachers are assigned one class (e.g. P3, S2). Null for other roles.
    class_level = db.Column(db.String(10), nullable=True)
    stream = db.Column(db.String(50), nullable=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(10), nullable=True)
    name = db.Column(db.String(100))
    class_level = db.Column(db.String(10), nullable=False, default="")
    stream = db.Column(db.String(50), nullable=True)
    rfid_tag = db.Column(db.String(100))
    photo_filename = db.Column(db.String(120), nullable=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    requested_by = db.Column(db.Integer)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')
    approved_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    time_out = db.Column(db.DateTime)
    time_in = db.Column(db.DateTime)
    guard_id = db.Column(db.Integer)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    kind = db.Column(db.String(30), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
