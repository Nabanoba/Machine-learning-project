from feature_engine import extract_features
from solver import solve_question
import re


def normalize(value):
    try:
        if isinstance(value, str) and "/" in value:
            n, d = value.split("/")
            return float(n) / float(d)
        return float(value)
    except:
        return str(value).strip().lower()


def extract_student_parts(text):
    parts = {}
    matches = re.findall(r'([a-eA-E])\s*=\s*([0-9/\.]+)', text)
    for k, v in matches:
        parts[k.lower()] = v
    return parts


def extract_numbers(text):
    return re.findall(r'\d+\.?\d*', text)


def evaluate_answer(question, student_answer):

    solution = solve_question(question)
    features = extract_features(student_answer)

    if not solution:
        return {
            "question": question,
            "expected_answer": "Not supported",
            "student_answer": student_answer,
            "score": 0,
            "competency": "Unknown",
            "feedback": ["Cannot solve this question"],
            **features
        }

    feedback = []
    score = 0

    # =========================
    # MULTI-PART
    # =========================
    if isinstance(solution, dict) and len(solution) > 1:

        student_parts = extract_student_parts(student_answer)
        correct = 0
        expected = solution

        for k, v in solution.items():

            s = student_parts.get(k)

            if not s:
                feedback.append(f"{k})  Missing (Correct: {v})")
                continue

            if abs(normalize(s) - normalize(v)) < 0.01:
                correct += 1
                feedback.append(f"{k}) Correct")
            else:
                feedback.append(f"{k}) {s} | Correct: {v}")

        score = int((correct / len(solution)) * 100)

    # =========================
    # SINGLE ANSWER
    # =========================
    else:

        correct = solution.get("answer")
        expected = correct

        try:
            if any(abs(normalize(n) - normalize(correct)) < 0.01 for n in extract_numbers(student_answer)):
                score = 80
                feedback.append("✅ Correct answer")
            else:
                score = 0
                feedback.append(f"❌ Correct answer is {correct}")
        except:
            score = 0
            feedback.append("❌ Invalid answer")

    # =========================
    # BONUS MARKS
    # =========================
    score += 3 if features["readability"] > 50 else 0
    score += 3 if features["lexical_diversity"] > 0.5 else 0
    score += 3 if features["avg_sentence_length"] > 5 else 0

    score = min(score, 100)

    # =========================
    # COMPETENCY
    # =========================
    if score >= 75:
        competency = "High"
    elif score >= 40:
        competency = "Medium"
    else:
        competency = "Low"

    return {
        "question": question,
        "expected_answer": expected,
        "student_answer": student_answer,
        "score": score,
        "competency": competency,
        "feedback": feedback,
        **features
    }