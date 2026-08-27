from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport

BRONZE = Path("dados/bronze")
PADRAO = "steam_games.csv"
RELATORIOS = Path("relatorios")

BRONZE_MUNDIAL = Path("dados/bronze/banco_mundial")
PADRAO_MUNDIAL = "paises_20260827.csv"

def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError("bronze vazia")
    return arquivos[-1]

def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida

def main():
    caminho = mais_recente(BRONZE, PADRAO)
    print("perfilando...", caminho.name)
    print(gerar(caminho))

if __name__ == "__main__":

    caminho = mais_recente(BRONZE_MUNDIAL, PADRAO_MUNDIAL)
    print("perfilando...", caminho.name)
    print(gerar(caminho))