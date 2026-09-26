import pandas as pd
from pathlib import Path

BRONZE_STEAM = Path("dados/bronze/steam")
PADRAO_STEAM = "steam_games_*.csv" 

BRONZE_MUNDIAL = Path("dados/bronze/banco_mundial")
PADRAO_MUNDIAL = "world_bank_development_indicators*.csv" 

def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"A pasta {path} está vazia ou o arquivo não foi encontrado.")
    return arquivos[-1]

def conferir_estrutura(caminho):
    print(f"\n{'='*50}")
    print(f"Analisando arquivo: {caminho.name}")
    print(f"{'='*50}")
    
    df = pd.read_csv(caminho, low_memory=False)
    
    print("Shape (linhas, colunas):", df.shape)
    
    print("\nLista exata de colunas (com aspas):")
    for coluna in df.columns:
        print(f'"{coluna}"')

def main():
    caminho_steam = mais_recente(BRONZE_STEAM, PADRAO_STEAM)
    conferir_estrutura(caminho_steam)
    
    caminho_mundial = mais_recente(BRONZE_MUNDIAL, PADRAO_MUNDIAL)
    conferir_estrutura(caminho_mundial)

if __name__ == "__main__":
    main()