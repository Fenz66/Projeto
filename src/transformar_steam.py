import json
import logging
from datetime import datetime

import pandas as pd

import limpeza
from config import BRONZE, PRATA, configurar_log

log = logging.getLogger(__name__)

ORIGEM = BRONZE / "steam"
PADRAO = "steam_games_*.csv"


def carregar():
    arquivos = sorted(ORIGEM.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"Nada encontrado em {ORIGEM}")
    caminho = arquivos[-1]

    colunas_uteis = ["app_id", "name", "price"]
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)
    log.info("steam: lido %s %s", caminho.name, df.shape)
    return df, caminho


def conferir_chave(df, chave="app_id"):
    repetidas = int(df[chave].duplicated().sum())
    if repetidas:
        log.warning("steam: %d chaves repetidas em '%s' removidas", repetidas, chave)
        df = df.drop_duplicates(subset=chave).copy()
    else:
        log.info("steam: 0 chaves repetidas em '%s'", chave)
    return df, repetidas


def tratar_precos(df, coluna_preco="price"):
    df = df.copy()
    df[coluna_preco] = pd.to_numeric(df[coluna_preco], errors="coerce")

    antes = len(df)
    df = df.dropna(subset=[coluna_preco]).copy()
    removidos = antes - len(df)
    if removidos:
        log.warning("steam: %d jogos removidos por preço vazio/inválido", removidos)
    return df, removidos


def tratar_nomes(df, coluna_nome="name"):
    antes = len(df)
    invalido = df[coluna_nome].isna() | (df[coluna_nome].astype(str).str.strip() == "")
    df = df.loc[~invalido].copy()
    removidos = antes - len(df)
    if removidos:
        log.warning("steam: %d jogos removidos por nome vazio/nulo", removidos)
    return df, removidos


def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def marcar_extremos(df, coluna="price"):
    df = df.copy()
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (df[coluna] < baixo) | (df[coluna] > alto)
    extremos = int(df[coluna + "_extremo"].sum())
    log.info("steam: %d extremos marcados em '%s' (IQR [%.2f, %.2f])", extremos, coluna, baixo, alto)
    return df, extremos


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "steam.parquet"
    df.to_parquet(destino, index=False)
    log.info("steam: salvo em %s %s", destino, df.shape)
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
    df, duplicatas = conferir_chave(df, chave="app_id")
    df, sem_preco = tratar_precos(df, coluna_preco="price")
    df, sem_nome = tratar_nomes(df, coluna_nome="name")
    df, extremos = marcar_extremos(df, coluna="price")

    destino = salvar(df)
    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Filtro aplicado para manter apenas as colunas relevantes (app_id, name, price)",
            "Espaços em branco removidos de nomes de colunas e strings",
            f"Duplicatas verificadas pela chave primária app_id ({duplicatas} removidas)",
            f"Preços inválidos convertidos a nulo e removidos ({sem_preco} removidos)",
            f"Jogos sem nome válido removidos ({sem_nome} removidos)",
            f"Outliers de preço marcados via método IQR sem exclusão ({extremos} marcados em price_extremo)",
        ],
    )


if __name__ == "__main__":
    configurar_log()
    main()
