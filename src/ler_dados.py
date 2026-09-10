import pandas as pd

# Atualize esta data para o dia em que o arquivo foi baixado!
CAMINHO = "dados/bronze/steam/steam_games_20260827.csv"

def carregar():
    return pd.read_csv(CAMINHO)

def conferir_estrutura(df):
    # 1. Quantas linhas e colunas existem?
    print("Shape:", df.shape)
    print("\nCinco primeiras linhas:")
    print(df.head())
    
    # 2. Quais são os tipos lidos?
    print("\nTipos das colunas:")
    print(df.dtypes)
    
    # 3. Revelando os espaços ocultos nas colunas
    print("\nNomes das colunas:")
    for coluna in df.columns:
        print(f'"{coluna}"')

if __name__ == "__main__":
    df = carregar()
    conferir_estrutura(df)