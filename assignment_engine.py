import pandas as pd

FILE = "ALL_with_features.xlsx"

def auto_assign_questions():
    df = pd.read_excel(FILE)

    # ensure clean column
    df.columns = df.columns.str.strip()

    # create column if missing
    if "Assigned_To" not in df.columns:
        df["Assigned_To"] = ""

    students = ["student1", "student2", "student3"]

    # -----------------------------
    # EASY QUESTIONS → student1
    # -----------------------------
    df.loc[df["DoK_Level"] <= 2, "Assigned_To"] = "student1"

    # -----------------------------
    # MEDIUM QUESTIONS → student2
    # -----------------------------
    df.loc[(df["DoK_Level"] > 2) & (df["DoK_Level"] <= 3), "Assigned_To"] = "student2"

    # -----------------------------
    # HARD QUESTIONS → student3
    # -----------------------------
    df.loc[df["DoK_Level"] > 3, "Assigned_To"] = "student3"

    # save back
    df.to_excel(FILE, index=False)

    return "Assignment Completed Successfully"