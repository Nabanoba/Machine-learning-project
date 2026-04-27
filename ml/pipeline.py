from ml.lda_model import run_lda
from ml.clustering import cluster_students
from ollama_engine import ask_llm


# =========================
# STEP 1: TOPIC (LDA)
# =========================
def get_topic(question):
    topics = run_lda([question])
    return int(topics.argmax(axis=1)[0])


# =========================
# STEP 2: RULE ENGINE (IMPORTANT)
# =========================
def rule_engine(question, answer):
    """
    Deterministic marking (NO AI here)
    """

    try:
        if "HARD" in question:
            correct = "H=12, A=1, R=11, D=4"
            score = 30 if "don't know" not in answer.lower() else 0
        else:
            correct = "To be computed"
            score = 20

        return correct, score

    except:
        return "Not computed", 0


# =========================
# STEP 3: CLUSTERING
# =========================
def get_cluster(scores):
    if len(scores) < 2:
        return [0] * len(scores)

    return cluster_students(scores)


# =========================
# STEP 4: OLLAMA FEEDBACK ONLY
# =========================
def get_feedback(question, answer, score):
    prompt = f"""
You are a mathematics teacher.

Give ONLY short feedback.

Question: {question}
Answer: {answer}
Score: {score}

Explain in 2-3 lines only.
"""

    return ask_llm(prompt)