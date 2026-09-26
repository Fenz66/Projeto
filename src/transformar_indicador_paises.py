import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import limpeza

BRONZE = Path("dados/bronze/banco_mundial")
PADRAO = "world_bank_development_indicators_*.csv"
PRATA = Path("dados/prata")

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    
    colunas_uteis = [
        "country", 
        "date",  
        "GDP_current_US", 
        "population"
    ]
    df = pd.read_csv(caminho, usecols=colunas_uteis)
    return df, caminho

def converter_tipos(df):
    df["date"] = pd.to_numeric(df["date"], errors="coerce")
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

def variacao_anual(df, chave, tempo, valor):
    
    df = df.sort_values([chave, tempo])
    df["variacao_pct_PIB"] = (df.groupby(chave)[valor].pct_change() * 100)
    return df

def faixa_por_quartil(df, coluna, rotulos):
    nova_coluna = coluna + "_faixa"
    df[nova_coluna] = pd.qcut(df[coluna], q=4, labels=rotulos, duplicates='drop')
    return df

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "banco_mundial.parquet"
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
    df = conferir_chave(df, chaves=["country", "date"])
    df = tratar_vazios(df)
    df = limpeza.tirar_espacos(df)
    df = faixa_por_quartil(
        df, 
        "population",
        ["muito pequeno", "pequeno", "grande", "muito grande"]
    )
    
    df = variacao_anual(df, chave="country", tempo="date", valor="GDP_current_US")
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "Filtro aplicado para manter apenas colunas econômicas (PIB e População)",
        "Coluna 'date' convertida para numérico (inteiro)",
        "Duplicatas verificadas pela chave composta país + ano",
        "Anos/Países sem dados de PIB ou População foram removidos",
        "Espaços removidos das strings (limpeza)",
        "Atributo derivado criado: Faixa de população por quartil",
        "Atributo derivado criado: Variação percentual anual do PIB"
    ])
    print("Transformação do Banco Mundial concluída!")

if __name__ == "__main__":
    main()