import pandas as pd

df = pd.read_excel("ALL_with_features.xlsx")

#  FIX: force column to text
df["Assigned_To"] = df["Assigned_To"].astype(str)

# assign students
df.loc[0:10, "Assigned_To"] = "student1"

df.to_excel("ALL_with_features.xlsx", index=False)

print("Assignment successful")