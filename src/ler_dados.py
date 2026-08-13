import pandas as pd

CAMINHO = "./dados/bronze/"

df = pd.read_csv(CAMINHO)

print(df.shape)
print(df.head())
print(df.columns)

print(df.shape)

for coluna in df.columns:
    print(f"{coluna}: {df(coluna).dtype}")