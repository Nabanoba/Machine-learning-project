from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import re
import numpy as np
import os
import json
from model_engine import evaluate_answer
from database import register_user, login_user, get_all_students
from assignment_engine import auto_assign_questions

from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from flask_migrate import Migrate

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
app = Flask(__name__)
app.secret_key = "AI_COMPETENCY_SYSTEM_2026"

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    db_url = os.getenv("DATABASE_URL")

    # Render fix
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///local.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    return app

app = create_app()
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

# HOME
@app.route('/')
def home():
    return redirect(url_for('login'))

# LOGIN
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
            else:
                return redirect(url_for('student_dashboard'))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        success = register_user(username, password, role)

        if success:
            return redirect(url_for('login'))
        else:
            return render_template("register.html", error="User already exists")

    return render_template("register.html")

# NORMALIZER
def normalize_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text

# EVALUATE ROUTE
@app.route('/evaluate', methods=['POST'])
def evaluate():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    

    # GET FORM DATA
    
    question = request.form.get('question', '')
    answer = request.form.get('answer', '')
    item_id = request.form.get('item_id')
    student = session.get("user")

    # LOAD DATASET

    try:
        df = pd.read_excel("ALL_with_features.xlsx")
        df.columns = df.columns.str.strip().str.lower()
    except:
        df = pd.DataFrame()

    row = df[df["item_id"].astype(str) == str(item_id)] if "item_id" in df.columns else pd.DataFrame()

    if not row.empty:
        row = row.iloc[0]
        construct = row.get("construct", "N/A")
        correct_answer = str(row.get("correct_answer", "")).strip()
        bloom_raw = row.get("bloom_level", "")
        dok_raw = row.get("dok_level", "")
    else:
        construct = "N/A"
        correct_answer = ""
        bloom_raw = ""
        dok_raw = ""

    
    # ENCODE BLOOM & DOK
    bloom_map = {
        "remember": 1,
        "understand": 2,
        "apply": 3,
        "analyse": 4,
        "analyze": 4,
        "evaluate": 5,
        "create": 6
    }

    def encode_level(x):
        return bloom_map.get(str(x).strip().lower(), 0) if x else 0

    bloom = float(encode_level(bloom_raw))
    dok = float(encode_level(dok_raw))

    
    # TEXT FEATURES
    
    text = str(answer)

    readability = float(len(text.split()))

    sentences = re.split(r'[.!?]', text)
    sentences = [s for s in sentences if s.strip()]

    if sentences:
        avg_sentence_length = float(np.mean([len(s.split()) for s in sentences]))
    else:
        avg_sentence_length = readability

    
    # NORMALIZATION
    
    def normalize(x):
        return str(x).strip().lower().replace(" ", "")

    student_clean = normalize(answer)

    
    # INITIAL SCORING
    
    score = 0

    if student_clean in ["", "idontknow", "idonotknow", "unknown"]:
        score = 0
    else:
        try:
            student_json = json.loads(answer.replace("'", '"'))
            correct_json = json.loads(correct_answer.replace("'", '"'))

            total = len(correct_json)
            correct_count = 0

            for key in correct_json:
                if key in student_json:
                    if normalize(student_json[key]) == normalize(correct_json[key]):
                        correct_count += 1

            score = (correct_count / total) * 100 if total > 0 else 0

        except:
            if normalize(answer) == normalize(correct_answer):
                score = 100
            else:
                score = min(100, readability * 5)

    # CLEAN SCORE
    
    try:
        score = float(score)
        if np.isnan(score):
            score = 0
    except:
        score = 0

    
    # AI WEIGHTED SCORING
    
    if student_clean not in ["", "idontknow", "idonotknow", "unknown"]:
        correctness = score / 100

        score = (
            0.6 * correctness +
            0.2 * min(readability / 50, 1) +
            0.2 * min(avg_sentence_length / 20, 1)
        ) * 100

        score = max(0, min(100, float(score)))
    else:
        score = 0

    
    # COMPETENCY
    
    if score >= 70:
        competency = "High"
        explanation = "Strong understanding with accurate responses."
    elif score >= 40:
        competency = "Medium"
        explanation = "Partial understanding. Improve clarity."
    else:
        competency = "Low"
        explanation = "Needs improvement. Review the concept."

    feedback = {
        "status": competency,
        "explanation": explanation
    }

    
    # FEATURE VECTOR

    feature_vector = [
        float(readability),
        float(bloom),
        float(dok),
        float(avg_sentence_length)
    ]

    
    # STORE IN POSTGRESQL

    new_result = Result(
        student=student,
        question=question,
        student_answer=answer,
        correct_answer=correct_answer,
        score=score,
        competency=competency,
        construct=construct,
        bloom=bloom,
        dok=dok,
        readability=readability,
        avg_sentence_length=avg_sentence_length,
        feature_vector=json.dumps(feature_vector),
        cluster="Not assigned yet"
    )

    db.session.add(new_result)
    db.session.commit()

    return redirect(url_for('student_done'))

# STUDENT DONE PAGE
@app.route('/student_done')
def student_done():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_template("submitted.html")

@app.route('/teacher')
def teacher_dashboard():

    if session.get('role') != 'teacher':
        return redirect(url_for('login'))

    df = pd.read_excel("ALL_with_features.xlsx")

    # CLEAN EVERYTHING
    df.columns = df.columns.str.strip().str.lower()

    # ensure no NaN issues
    df = df.fillna("")

    search = request.args.get("search", "").strip().lower()

    questions = df.copy()

    # FILTER BY CONSTRUCT
    if search:
        questions = questions[
            questions["construct"].astype(str).str.lower().str.contains(search)
        ]

    # KEEP ONLY NEEDED FIELDS
    questions = questions[[
        "item_id",
        "item",
        "construct",
        "bloom_level",
        "dok_level",
        "assigned_to"
    ]].to_dict(orient="records")

    students = get_all_students()

    return render_template(
        "teacher_dashboard.html",
        questions=questions,
        students=students,
        search=search
    )


# CLUSTER RESULTS (AGGLOMERATIVE)
@app.route('/teacher/results')
def teacher_results():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    
    try:
        results = Result.query.all()
    except Exception as e:
        return f"Database error: {str(e)}"

    results_store = []

    #  use "results" not "results_query"
    for r in results:

        # safely parse feedback
        try:
            feedback = json.loads(r.feedback) if r.feedback else {}
        except:
            feedback = {}

        results_store.append({
            "student": str(r.student or ""),
            "question": str(r.question or ""),
            "student_answer": str(r.student_answer or ""),
            "correct_answer": str(r.correct_answer or ""),
            "score": float(r.score or 0),
            "competency": str(r.competency or "Low"),
            "feedback": feedback,
            "dok": float(r.dok or 0),
            "readability": float(r.readability or 0),
            "avg_sentence_length": float(r.avg_sentence_length or 0),
            "cluster": r.cluster or "Not assigned"
        })

    n = len(results_store)

    if n == 0:
        return render_template("result.html", results=[])

    # DEFAULT CLUSTER
    for r in results_store:
        r["cluster"] = "Low Performer"

    if n >= 2:

        X = np.array([
            [
                float(r.get("score") or 0),
                len(str(r.get("student_answer") or "").split()),
                len(str(r.get("question") or "").split()),
                float(r.get("dok") or 0)
            ]
            for r in results_store
        ])

        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(X)

        from sklearn.cluster import AgglomerativeClustering
        model = AgglomerativeClustering(
            n_clusters=min(3, n),
            linkage="ward"
        )

        labels = model.fit_predict(X)

        for i, r in enumerate(results_store):
            r["cluster_raw"] = int(labels[i])

        cluster_avg = {}

        for c in set(labels):
            cluster_avg[c] = np.mean([
                float(r["score"] or 0)
                for r in results_store
                if r["cluster_raw"] == c
            ])

        sorted_clusters = sorted(cluster_avg, key=cluster_avg.get)

        names = ["Low Performer", "Average Performer", "High Performer"]

        cluster_map = {
            c: names[i] for i, c in enumerate(sorted_clusters)
            if i < len(names)
        }

        for r in results_store:
            r["cluster"] = cluster_map.get(r["cluster_raw"], "Low Performer")
            del r["cluster_raw"]

            db_result = Result.query.filter_by(
                student=r["student"],
                question=r["question"]
            ).first()

            if db_result:
                db_result.cluster = r["cluster"]

        db.session.commit()

    return render_template("result.html", results=results_store)


@app.route('/assign/<item_id>')
def assign_question(item_id):

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    import os
    import pandas as pd

    student = request.args.get("student")

    if not student:
        return "No student selected"

    # Load dataset safely
    file_path = os.path.join(os.path.dirname(__file__), "ALL_with_features.xlsx")

    if not os.path.exists(file_path):
        return "Dataset file not found"

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()

    # Ensure column exists
    if "assigned_to" not in df.columns:
        df["assigned_to"] = ""

    # Assign student
    df.loc[df["item_id"].astype(str) == str(item_id), "assigned_to"] = student.lower()

    # Save back
    df.to_excel(file_path, index=False)

    return redirect(url_for('teacher_dashboard'))

@app.route('/student')
def student_dashboard():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    username = str(session.get("user")).lower()

    df = pd.read_excel("ALL_with_features.xlsx")

    df.columns = df.columns.str.strip().str.lower()

    if "assigned_to" not in df.columns:
        df["assigned_to"] = ""

    df["assigned_to"] = df["assigned_to"].fillna("").astype(str).str.lower()

    student_questions = df[
        df["assigned_to"] == username
    ].to_dict(orient="records")

    return render_template(
        "student_dashboard.html",
        questions=student_questions,
        username=username
    )


@app.route('/teacher/student-dashboard-stats')
def student_dashboard_stats():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    import pandas as pd

    results = Result.query.all()

    if not results:
        return render_template("student_stats.html", stats=[])

    data = []

    for r in results:
        data.append({
            "student": str(r.student or "unknown"),
            "readability": float(r.readability or 0),
            "avg_sentence_length": float(r.avg_sentence_length or 0),
            "competency": str(r.competency or "Low"),
            "score": float(r.score or 0)
        })

    df = pd.DataFrame(data)

    if df.empty:
        return render_template("student_stats.html", stats=[])

    # CLEAN
    df["readability"] = pd.to_numeric(df["readability"], errors="coerce").fillna(0)
    df["avg_sentence_length"] = pd.to_numeric(df["avg_sentence_length"], errors="coerce").fillna(0)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)

    # GROUP
    summary = df.groupby("student").agg(
        Attempts=("student", "count"),
        Avg_Readability=("readability", "mean"),
        Avg_Sentence_Length=("avg_sentence_length", "mean"),
        High=("competency", lambda x: (x == "High").sum()),
        Medium=("competency", lambda x: (x == "Medium").sum()),
        Low=("competency", lambda x: (x == "Low").sum()),
    ).reset_index()

    summary["Avg_Readability"] = summary["Avg_Readability"].round(2)
    summary["Avg_Sentence_Length"] = summary["Avg_Sentence_Length"].round(2)

    return render_template(
        "student_stats.html",
        stats=summary.to_dict(orient="records")
    )

# AUTO ASSIGN
@app.route("/auto_assign")
def auto_assign():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return auto_assign_questions()

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# FORGOT PASSWORD
@app.route('/forgot-password')
def forgot_password():
    return render_template("forgot_password.html")


@app.route('/teacher/cluster-visualization')
def cluster_visualization():

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    
    results = Result.query.all()

    if len(results) < 2:
        return "Not enough data for visualization"

    X = np.array([
        [
            float(r.score or 0),
            len(str(r.student_answer or "").split()),
            float(r.readability or 0)
        ]
        for r in results
    ])

    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(X)

    from sklearn.cluster import AgglomerativeClustering
    model = AgglomerativeClustering(
        n_clusters=min(3, len(results)),
        linkage="ward"
    )

    labels = model.fit_predict(X)

    from sklearn.decomposition import PCA
    X_2d = PCA(n_components=2).fit_transform(X)

    #  ensure static folder exists
    static_path = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_path, exist_ok=True)

    image_path = os.path.join(static_path, "cluster_plot.png")

    plt.figure()
    plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels)
    plt.title("Student Performance Clusters")

    plt.savefig(image_path)
    plt.close()

    return render_template("cluster_view.html", image_path="static/cluster_plot.png")


# RUN APP
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    