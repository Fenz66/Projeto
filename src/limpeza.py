"""Funções de limpeza genéricas que servem a qualquer fonte."""

import pandas as pd


def tirar_espacos(df):
    """Remove espaços sobrando nos nomes das colunas e em colunas de texto."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    for c in df.select_dtypes(include=["object", "string"]):
        df[c] = df[c].str.strip()
    return df


def chave_texto(serie):
    """Versão comparável de um texto: sem acento, sem espaço sobrando e em minúsculas."""
    s = serie.str.strip().str.lower()
    s = s.str.normalize("NFKD")
    s = s.str.encode("ascii", errors="ignore")
    return s.str.decode("utf-8")


def aplicar_mapa(serie, mapa):
    """Troca variantes pelo valor canônico. O que não estiver no mapa fica como está."""
    return serie.replace(mapa)
