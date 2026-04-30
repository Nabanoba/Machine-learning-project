from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import json
import numpy as np
import pandas as pd
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from database import register_user, login_user, get_all_students
from assignment_engine import auto_assign_questions

app = Flask(__name__)
app.secret_key = "AI_COMPETENCY_SYSTEM_2026"

# ================= DATABASE =================
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app) 

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise Exception("DATABASE_URL missing")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

with app.app_context():
    db.create_all()

# ================= MODEL =================
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student = db.Column(db.String(100))
    question = db.Column(db.Text)
    student_answer = db.Column(db.Text)
    correct_answer = db.Column(db.Text)
    score = db.Column(db.Float)
    competency = db.Column(db.String(20))
    feedback = db.Column(db.Text)
    construct = db.Column(db.String(100))
    bloom = db.Column(db.Float)
    dok = db.Column(db.Float)
    readability = db.Column(db.Float)
    avg_sentence_length = db.Column(db.Float)
    feature_vector = db.Column(db.Text)
    cluster = db.Column(db.String(50))


# ================= HOME =================
@app.route('/')
def home():
    return redirect(url_for('login'))


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = login_user(username, password)

        if user:
            session['user'] = user[1]
            session['role'] = user[3]

            if user[3] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            return redirect(url_for('student_dashboard'))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        success = register_user(
            request.form.get('username'),
            request.form.get('password'),
            request.form.get('role')
        )

        if success:
            return redirect(url_for('login'))

        return render_template("register.html", error="User already exists")

    return render_template("register.html")


# ================= NORMALIZER =================
def normalize(x):
    return str(x).strip().lower().replace(" ", "")


# ================= EVALUATE =================
@app.route('/evaluate', methods=['POST'])
def evaluate():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    question = request.form.get('question', '')
    answer = request.form.get('answer', '')
    student = session.get("user")

    readability = len(str(answer).split())
    avg_sentence_length = readability

    score = 0
    if answer:
        score = min(100, readability * 5)

    competency = "High" if score > 70 else "Medium" if score > 40 else "Low"

    new_result = Result(
        student=student,
        question=question,
        student_answer=answer,
        correct_answer="",
        score=score,
        competency=competency,
        feedback=json.dumps({"status": competency}),
        construct="N/A",
        bloom=0,
        dok=0,
        readability=readability,
        avg_sentence_length=avg_sentence_length,
        feature_vector=json.dumps([]),
        cluster="Not assigned"
    )

    db.session.add(new_result)
    db.session.commit()

    return redirect(url_for('student_done'))


# ================= STUDENT DONE =================
@app.route('/student_done')
def student_done():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_template("submitted.html")


# ================= TEACHER DASHBOARD =================
@app.route('/teacher')
def teacher_dashboard():

    if session.get('role') != 'teacher':
        return redirect(url_for('login'))

    results = Result.query.all()

    return render_template("teacher_dashboard.html", results=results)


# ================= RESULTS =================
@app.route('/teacher/results')
def teacher_results():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    results = Result.query.all()

    output = []

    for r in results:

        try:
            feedback = json.loads(r.feedback) if r.feedback else {}
        except:
            feedback = {}

        output.append({
            "student": r.student,
            "question": r.question,
            "student_answer": r.student_answer,
            "correct_answer": r.correct_answer,
            "score": r.score,
            "competency": r.competency,
            "feedback": feedback,
            "cluster": r.cluster or "Not assigned"
        })

    return render_template("result.html", results=output)


# ================= CLUSTER =================
@app.route('/teacher/cluster-visualization')
def cluster_visualization():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    results = Result.query.all()

    if len(results) < 2:
        return "Not enough data"

    X = np.array([
        [
            float(r.score or 0),
            len(str(r.student_answer or "").split()),
            float(r.readability or 0)
        ]
        for r in results
    ])

    X = StandardScaler().fit_transform(X)

    labels = AgglomerativeClustering(
        n_clusters=min(3, len(results)),
        linkage="ward"
    ).fit_predict(X)

    X_2d = PCA(n_components=2).fit_transform(X)

    os.makedirs("static", exist_ok=True)
    path = "static/cluster_plot.png"

    plt.figure()
    plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels)
    plt.title("Student Clusters")
    plt.savefig(path)
    plt.close()

    return render_template("cluster_view.html", image_path=path)


# ================= STUDENT STATS =================
@app.route('/teacher/student-dashboard-stats')
def student_dashboard_stats():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    results = Result.query.all()

    data = [{
        "student": r.student,
        "readability": r.readability or 0,
        "avg_sentence_length": r.avg_sentence_length or 0,
        "competency": r.competency,
        "score": r.score or 0
    } for r in results]

    df = pd.DataFrame(data)

    if df.empty:
        return render_template("student_stats.html", stats=[])

    summary = df.groupby("student").agg(
        Attempts=("student", "count"),
        Avg_Readability=("readability", "mean"),
        Avg_Sentence_Length=("avg_sentence_length", "mean"),
        High=("competency", lambda x: (x == "High").sum()),
        Medium=("competency", lambda x: (x == "Medium").sum()),
        Low=("competency", lambda x: (x == "Low").sum()),
    ).reset_index()

    return render_template("student_stats.html", stats=summary.to_dict(orient="records"))


# ================= ASSIGN =================
@app.route('/assign/<item_id>')
def assign_question(item_id):

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    student = request.args.get("student")

    if not student:
        return "No student selected"

    return redirect(url_for('teacher_dashboard'))


# ================= STUDENT DASHBOARD =================
@app.route('/student')
def student_dashboard():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    username = session.get("user")

    results = Result.query.filter_by(student=username).all()

    return render_template("student_dashboard.html", questions=results)


# ================= AUTO ASSIGN =================
@app.route("/auto_assign")
def auto_assign():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    return auto_assign_questions()


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ================= FORGOT PASSWORD =================
@app.route('/forgot-password')
def forgot_password():
    return render_template("forgot_password.html")


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)