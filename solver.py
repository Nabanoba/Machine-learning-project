import json
import re

# =========================
# SIMPLE OFFLINE SOLVER
# =========================

def extract_json(text):
    """Extract JSON safely if needed"""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        return None


def solve_question(question):
    """
    Offline fallback solver (no AI API needed)
    You can later upgrade this with ML or rule-based logic.
    """

    try:
        question = str(question).lower()

        # =========================
        # SIMPLE MATH HANDLING
        # =========================

        # Example: addition
        if "+" in question:
            nums = re.findall(r"\d+", question)
            if len(nums) >= 2:
                answer = sum(map(int, nums))
                return {"answer": answer}

        # Example: subtraction
        if "-" in question:
            nums = re.findall(r"\d+", question)
            if len(nums) >= 2:
                answer = int(nums[0]) - int(nums[1])
                return {"answer": answer}

        # Example: multiplication
        if "x" in question or "*" in question:
            nums = re.findall(r"\d+", question)
            if len(nums) >= 2:
                answer = int(nums[0]) * int(nums[1])
                return {"answer": answer}

        # =========================
        # DEFAULT RESPONSE
        # =========================
        return {
            "answer": "Unable to solve automatically"
        }

    except Exception as e:
        print("Solver error:", e)
        return {
            "answer": "Error in solving"
        }