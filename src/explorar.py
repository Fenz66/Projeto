from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport

BRONZE_STEAM = Path("dados/bronze/steam")
PADRAO_STEAM = "steam_games_*.csv" 

BRONZE_MUNDIAL = Path("dados/bronze/banco_mundial")
PADRAO_MUNDIAL = "world_bank_development_indicators*.csv" 

BRONZE_INDICADOR = Path("dados/bronze/banco_mundial/indicador_paises")
PADRAO_INDICADOR = "*.csv" 

RELATORIOS = Path("relatorios")

def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"A pasta {path} está vazia ou o arquivo não foi encontrado.")
    return arquivos[-1]

def gerar(caminho):
    df = pd.read_csv(caminho, low_memory=False)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida

def main():
    caminho_steam = mais_recente(BRONZE_STEAM, PADRAO_STEAM)
    print("Perfilando:", caminho_steam.name)
    print("Salvo em:", gerar(caminho_steam))

    caminho_mundial = mais_recente(BRONZE_MUNDIAL, PADRAO_MUNDIAL)
    print("Perfilando:", caminho_mundial.name)
    print("Salvo em:", gerar(caminho_mundial))

    try:
        caminho_indicador = mais_recente(BRONZE_INDICADOR, PADRAO_INDICADOR)
        print("Perfilando:", caminho_indicador.name)
        print("Salvo em:", gerar(caminho_indicador))
    except FileNotFoundError:
        print(f"Nenhum arquivo encontrado em {BRONZE_INDICADOR}")

if __name__ == "__main__":
    main()