import json
import logging
from datetime import datetime

import pandas as pd

import config
import limpeza


def carregar():
    arquivos = sorted(config.BRONZE_STEAM.glob(config.PADRAO_STEAM))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo Steam encontrado em {config.BRONZE_STEAM}")
    caminho = arquivos[-1]

    colunas_uteis = ["app_id", "name", "price"]
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)

    logging.info("Lido arquivo Bronze Steam: %s %s", caminho.name, df.shape)
    return df, caminho


def conferir_chave(df, chave):
    repetidas = int(df[chave].duplicated().sum())
    logging.info("Chaves repetidas na coluna '%s': %d", chave, repetidas)
    if repetidas:
        df = df.drop_duplicates(subset=chave).copy()
    return df, repetidas


def tratar_precos(df, coluna_preco):
    df = df.copy()
    df[coluna_preco] = pd.to_numeric(df[coluna_preco], errors="coerce")

    antes = len(df)
    df = df.dropna(subset=[coluna_preco]).copy()
    removidos = antes - len(df)
    logging.info("Jogos removidos por falta de preço válido: %d", removidos)

    return df, removidos


def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def marcar_extremos(df, coluna):
    df = df.copy()
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (df[coluna] < baixo) | (df[coluna] > alto)
    extremos = int(df[coluna + "_extremo"].sum())
    logging.info(
        "Extremos marcados em '%s' (IQR [%.2f, %.2f]): %d",
        coluna,
        baixo,
        alto,
        extremos,
    )
    return df, extremos


def salvar(df):
    config.PRATA.mkdir(parents=True, exist_ok=True)
    destino = config.PRATA / "steam.parquet"
    df.to_parquet(destino, index=False)
    logging.info("Salvo em: %s %s", destino, df.shape)
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
    caminho = config.PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    logging.info("Proveniência da Prata atualizada em: %s", caminho)


def main():
    df, origem = carregar()
    antes = len(df)

    df = limpeza.tirar_espacos(df)
    df, duplicatas = conferir_chave(df, chave="app_id")
    df, sem_preco = tratar_precos(df, coluna_preco="price")
    df, extremos = marcar_extremos(df, coluna="price")

    destino = salvar(df)
    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Filtro aplicado para manter apenas as colunas relevantes ao Índice de Acessibilidade (app_id, name, price)",
            "Espaços em branco removidos dos nomes de colunas e strings",
            f"Duplicatas verificadas pela chave primária app_id ({duplicatas} removidas)",
            f"Preços inválidos forçados a nulo e valores vazios de preço removidos ({sem_preco} removidos)",
            f"Outliers de preço marcados via método IQR sem exclusão ({extremos} marcados em price_extremo)",
        ],
    )
    logging.info("Transformação da Steam concluída!")


if __name__ == "__main__":
    main()
