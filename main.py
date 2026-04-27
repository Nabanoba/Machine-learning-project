import pandas as pd

df = pd.read_excel("ALL_with_features.xlsx")
print(df.columns)
print(df[["Item", "Assigned_To"]].head(10))