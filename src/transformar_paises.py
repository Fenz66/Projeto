import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import limpeza

MAPA_PAISES = {
    "united states of america": "usa",
    "united states": "usa",
    "uk": "united kingdom"
    # Adicione aqui outros países que a Steam e o Banco Mundial escrevam diferente!
}

BRONZE = Path("dados/bronze/banco_mundial")
PRATA = Path("dados/prata")
PADRAO = "world_bank_development_indicators*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    
    colunas_uteis = [
        "country", 
        "date", 
        "GDP_current_US", 
        "population", 
        "inflation_annual%"
    ]
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)
    
    print("lido:", caminho.name, df.shape)
    return df, caminho

def converter_tipos(df):
    df["date"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
    return df

def conferir_chave(df, chaves):
    repetidas = df.duplicated(subset=chaves).sum()
    print(f"chaves repetidas na combinação {chaves}:", repetidas)
    if repetidas:
        df = df.drop_duplicates(subset=chaves)
    return df

def tratar_vazios(df):
    antes = len(df)
    df = df.dropna(subset=["GDP_current_US", "population"])
    removidos = antes - len(df)
    print(f"Linhas removidas por falta de PIB/População: {removidos}")
    return df.copy()

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "paises.parquet"
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
    
    df = converter_tipos(df)
    
    df = limpeza.tirar_espacos(df)
    
    if "country" in df.columns:
        df["country"] = limpeza.chave_texto(df["country"])
        df["country"] = limpeza.aplicar_mapa(df["country"], MAPA_PAISES)
    
    df = conferir_chave(df, chaves=["country", "date"])
    df = tratar_vazios(df)
    
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "Filtro aplicado para manter apenas colunas econômicas (PIB, População, Inflação)",
        "Coluna 'date' convertida para numérico inteiro (Int64)",
        "Espaços removidos das strings",
        "Nomes dos países padronizados (minúsculas, sem acento) e mapeados via dicionário explícito",
        "Duplicatas verificadas pela chave composta país + ano",
        "Anos/Países sem dados de PIB ou População foram removidos"
    ])
    print("Transformação do Banco Mundial concluída!")

if __name__ == "__main__":
    main()