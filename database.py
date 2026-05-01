from models import User
from extensions import db


# REGISTER USER
def register_user(username, password, role):
    username = username.strip().lower()
    role = role.strip().lower()

    existing = User.query.filter_by(username=username).first()
    if existing:
        return False

    user = User(
        username=username,
        password=password,
        role=role
    )

    db.session.add(user)
    db.session.commit()
    return True


# LOGIN USER

def login_user(username, password):
    username = username.strip().lower()

    user = User.query.filter_by(
        username=username,
        password=password
    ).first()

    if user:
        return (user.id, user.username, user.password, user.role)

    return None



# GET ALL STUDENTS
def get_all_students():
    students = User.query.filter_by(role="student").all()
    return [{"username": s.username} for s in students]