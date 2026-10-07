import pandas as pd;

df = pd.read_csv("/Users/pol/Pol/polito/magistrale /AI/labs/AI-Cybersecurity_labs2026/Lab_01/Materiale/dataset_lab_1.csv")
print(df['Label'])

df = df.dropna()
df = df.drop_duplicates()
print(df['Label'])
