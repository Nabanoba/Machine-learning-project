from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import re
import numpy as np
import os
import json
import json
from model_engine import evaluate_answer
from database import register_user, login_user, get_all_students
from assignment_engine import auto_assign_questions

from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler

import matplotlib
matplotlib.use('Agg')

import numpy as np
from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)
app.secret_key = "AI_COMPETENCY_SYSTEM_2026"


import ast

# LOAD RESULTS SAFELY

try:
    df = pd.read_excel("results.xlsx")

    def safe_parse(val):
        try:
            if isinstance(val, str):
                return ast.literal_eval(val)
            return val
        except:
            return {"status": "Not available", "explanation": "Not available"}

    df["feedback"] = df["feedback"].apply(safe_parse)
    df["correct_answer"] = df["correct_answer"].apply(safe_parse)

    results_store = df.to_dict(orient="records")

except:
    results_store = []
    
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

    question = request.form.get('question')
    answer = request.form.get('answer')
    item_id = request.form.get('item_id')
    student = session.get("user")

    # LOAD DATASET
    df = pd.read_excel("ALL_with_features.xlsx")
    df.columns = df.columns.str.strip().str.lower()

    row = df[df["item_id"].astype(str) == str(item_id)]

    if not row.empty:
        row = row.iloc[0]
        construct = row.get("construct", "N/A")
        bloom = row.get("bloom_level", "N/A")
        dok = row.get("dok_level", "N/A")
        correct_answer = row.get("correct_answer", "Not available")
    else:
        construct = bloom = dok = "N/A"
        correct_answer = "Not available"

    # GRADING LOGIC (FIXED)

    import json
    import re

    try:
        correct_dict = json.loads(str(correct_answer).replace("'", '"'))
    except:
        correct_dict = {}

    def parse_student(ans):
        pairs = re.findall(r"([a-z])\s*[:=]\s*([^\s,]+)", str(ans).lower())
        return dict(pairs)

    student_dict = parse_student(answer)

    total = len(correct_dict) if correct_dict else 1
    correct_count = 0

    for key, value in correct_dict.items():
        student_value = student_dict.get(key, "").strip()

        if student_value == str(value).strip():
            correct_count += 1

    score = int((correct_count / total) * 100)

    # FEEDBACK LOGIC
    
    if score == 100:
        competency = "High"
        feedback = {
            "status": "Correct",
            "explanation": "Excellent work! All answers are correct."
        }

    elif score >= 50:
        competency = "Medium"
        feedback = {
            "status": "Partially Correct",
            "explanation": "You got some parts correct. Review the rest."
        }

    else:
        competency = "Low"
        feedback = {
            "status": "Incorrect",
            "explanation": "Revise the concept and try again."
        }

    # STORE RESULT
    results_store.append({
        "student": student,
        "question": question,
        "student_answer": answer,
        "correct_answer": correct_answer,
        "feedback": feedback,
        "score": score,
        "competency": competency,
        "construct": construct,
        "bloom": bloom,
        "dok": dok,
        "readability": len(str(answer).split()),
        "cluster": None
    })

    # SAVE TO EXCEL
    pd.DataFrame(results_store).to_excel("results.xlsx", index=False)

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

    n = len(results_store)


# ALWAYS SHOW RESULTS
    if n == 0:
        return render_template("result.html", results=[])

    # default fallback
    for r in results_store:
        r["cluster"] = "Low Performer"

    # ONLY CLUSTER IF ENOUGH DATA
    if n >= 2:

        X = np.array([
    [
        r.get("score", 0),
        len(str(r.get("student_answer", "")).split()),
        len(str(r.get("question", "")).split()),
        r.get("dok", 0) if isinstance(r.get("dok", 0), (int, float)) else 0
    ]
    for r in results_store
])

        X = StandardScaler().fit_transform(X)

        n_clusters = min(3, n)

        model = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
        labels = model.fit_predict(X)

        # attach raw labels
        for i, r in enumerate(results_store):
            r["cluster_raw"] = int(labels[i])

        # compute performance ranking
        cluster_avg = {}

        for c in set(labels):
            cluster_avg[c] = np.mean([
                r.get("score", 0)
                for r in results_store
                if r["cluster_raw"] == c
            ])

        sorted_clusters = sorted(cluster_avg, key=cluster_avg.get)

        names = ["Low Performer", "Average Performer", "High Performer"]

        cluster_map = {
            c: names[i] for i, c in enumerate(sorted_clusters)
            if i < len(names)
        }

        # final assignment
        for r in results_store:
            r["cluster"] = cluster_map.get(r["cluster_raw"], "Low Performer")
            del r["cluster_raw"]

    return render_template("result.html", results=results_store)

@app.route('/assign/<item_id>')
def assign_question(item_id):

    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    student = request.args.get("student")

    df = pd.read_excel("ALL_with_features.xlsx")
    df.columns = df.columns.str.strip().str.lower()

    df.loc[df["item_id"].astype(str) == str(item_id), "assigned_to"] = str(student).lower()

    df.to_excel("ALL_with_features.xlsx", index=False)

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

    if len(results_store) == 0:
        return render_template("student_stats.html", stats=[])

    df = pd.DataFrame(results_store)

    summary = df.groupby("student").agg(
        avg_score=("score", "mean"),
        max_score=("score", "max"),
        min_score=("score", "min"),
        attempts=("score", "count")
    ).reset_index()

    comp = df.groupby(["student", "competency"]).size().unstack(fill_value=0)

    summary = summary.join(comp, on="student").fillna(0)

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

    if len(results_store) < 2:
        return "Not enough data for visualization"

    X = np.array([
        [
            r.get("score", 0),
            len(str(r.get("student_answer", "")).split()),
            r.get("readability", 0)
        ]
        for r in results_store
    ])

    X = StandardScaler().fit_transform(X)

    model = AgglomerativeClustering(n_clusters=min(3, len(results_store)), linkage="ward")
    labels = model.fit_predict(X)

    # 2D visualization (PCA)
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)

    import matplotlib.pyplot as plt

    plt.figure()
    plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels)

    plt.title("Student Performance Clusters")
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")

    path = "static/cluster_plot.png"
    plt.savefig(path)
    plt.close()

    return render_template("cluster_view.html", image_path=path)


# RUN APP
if __name__ == '__main__':
    app.run(debug=True)