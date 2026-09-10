from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport

# Caminhos isolados e padrões com o curinga (*) para ler a data
BRONZE_STEAM = Path("dados/bronze/steam")
PADRAO_STEAM = "steam_games_*.csv" 

BRONZE_MUNDIAL = Path("dados/bronze/banco_mundial")
PADRAO_MUNDIAL = "world_bank_development_indicators_*.csv" 

RELATORIOS = Path("relatorios")

def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"A pasta {path} está vazia ou o arquivo não foi encontrado.")
    return arquivos[-1]

def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida

def main():
    # Perfilando a primeira fonte (Steam)
    caminho_steam = mais_recente(BRONZE_STEAM, PADRAO_STEAM)
    print("Perfilando:", caminho_steam.name)
    print("Salvo em:", gerar(caminho_steam))

    # Perfilando a segunda fonte (Banco Mundial)
    caminho_mundial = mais_recente(BRONZE_MUNDIAL, PADRAO_MUNDIAL)
    print("Perfilando:", caminho_mundial.name)
    print("Salvo em:", gerar(caminho_mundial))

if __name__ == "__main__":
    main()