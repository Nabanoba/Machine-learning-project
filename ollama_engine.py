import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:latest"


# =========================
# CALL OLLAMA SAFELY
# =========================
def ask_llm(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=600
        )

        if response.status_code != 200:
            print("HTTP ERROR:", response.text)
            return ""

        data = response.json()
        return data.get("response", "").strip()

    except Exception as e:
        print("OLLAMA REQUEST ERROR:", str(e))
        return ""


# =========================
# SAFE JSON EXTRACTION
# =========================
def extract_json(text):
    try:
        if not text:
            return None

        # remove markdown noise
        text = text.replace("```json", "").replace("```", "").strip()

        # extract JSON block safely
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            return None

        json_str = text[start:end + 1]
        return json.loads(json_str)

    except Exception as e:
        print("JSON PARSE ERROR:", e)
        return None


# =========================
# SAFE SCORING
# =========================
def safe_score(value):
    try:
        value = int(value)
        return max(0, min(100, value))
    except:
        return 0


# =========================
# FALLBACK SCORE
# =========================
def fallback_score(answer):
    if not answer or answer.lower().strip() in ["i don't know", "idonot know", "", "none"]:
        return 0
    return 40


# =========================
# MAIN EVALUATION ENGINE
# =========================
def evaluate_answer(question, student_answer):

    prompt = f"""
You are a strict mathematics examiner.

Return ONLY valid JSON (no explanation, no markdown):

{{
  "correct_answer": "",
  "score": 0,
  "competency": "Low/Medium/High",
  "feedback": ""
}}

QUESTION:
{question}

STUDENT ANSWER:
{student_answer}
"""

    raw = ask_llm(prompt)
    data = extract_json(raw)

    # =========================
    # HARD SAFETY FIX
    # =========================
    if data is None:
        return {
            "correct_answer": "Not generated",
            "score": fallback_score(student_answer),
            "competency": "Low",
            "feedback": "AI failed or returned invalid response"
        }

    return {
        "correct_answer": str(data.get("correct_answer", "Not generated")),
        "score": safe_score(data.get("score", 0)),
        "competency": str(data.get("competency", "Low")),
        "feedback": str(data.get("feedback", ""))
    }


# =========================
# QUESTION GENERATION
# =========================
def generate_question(construct):

    prompt = f"""
Generate a competency-based mathematics question.

Construct: {construct}

Rules:
- real-life context
- multi-step problem
- include (a), (b), (c)

Return ONLY the question text.
"""

    return ask_llm(prompt)