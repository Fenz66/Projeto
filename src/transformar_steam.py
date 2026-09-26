
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import limpeza

BRONZE = Path("dados/bronze/steam")
PRATA = Path("dados/prata")
PADRAO = "steam_games*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    
    colunas_uteis = ["app_id", "name", "price"] 
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)
    
    print("lido:", caminho.name, df.shape)
    return df, caminho

def conferir_chave(df, chave):
    repetidas = df[chave].duplicated().sum()
    print(f"chaves repetidas na coluna '{chave}':", repetidas)
    if repetidas:
        df = df.drop_duplicates(subset=chave)
    return df

def tratar_precos(df, coluna_preco):
    df[coluna_preco] = pd.to_numeric(df[coluna_preco], errors="coerce")
    
    antes = len(df)
    df = df.dropna(subset=[coluna_preco])
    removidos = antes - len(df)
    print(f"Jogos removidos por falta de preço: {removidos}")
    
    return df.copy()

def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = ((df[coluna] < baixo) | (df[coluna] > alto))
    print(f"Extremos marcados em {coluna}:", df[coluna + "_extremo"].sum())
    return df

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "steam.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")

def main():
    df, origem = carregar()
    antes = len(df)
    
    df = limpeza.tirar_espacos(df)
    
    df = conferir_chave(df, chave="app_id")
    df = tratar_precos(df, coluna_preco="price")
    
    df = marcar_extremos(df, coluna="price")
    
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "Filtro aplicado para manter apenas as colunas relevantes ao Índice de Acessibilidade",
        "Espaços em branco removidos das strings",
        "Duplicatas tratadas pela chave AppID",
        "Preços inválidos forçados a nulo e valores vazios de preço removidos",
        "Outliers de preço marcados via método IQR"
    ])
    print("Transformação da Steam concluída!")

if __name__ == "__main__":
    main()