from extensions import db   # ONLY if app.py exists at root

class Result(db.Model):
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
    feedback_status = db.Column(db.String(20))
feedback_explanation = db.Column(db.Text)