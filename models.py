from extensions import db   # ONLY if app.py exists at root

class Result(db.Model):
    __tablename__ = "result"
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(100))
    question = db.Column(db.Text)
    student_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    score = db.Column(db.Float)
    competency = db.Column(db.String(20))
    construct = db.Column(db.String(100))
    bloom = db.Column(db.Float)
    dok = db.Column(db.Float)
    readability = db.Column(db.Float)
    avg_sentence_length = db.Column(db.Float)
    feature_vector = db.Column(db.Text)
    cluster = db.Column(db.String(50))
    feedback = db.Column(db.Text)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))   