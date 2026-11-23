import json
import logging
from datetime import datetime

import pandas as pd

import limpeza
from config import BRONZE, PRATA, configurar_log

log = logging.getLogger(__name__)

ORIGEM = BRONZE / "banco_mundial"
PADRAO = "world_bank_development_indicators_*.csv"

MAPA_PAISES = {
    "united states of america": "usa",
    "united states": "usa",
    "uk": "united kingdom",
    "czech republic": "czechia",
    "turkey": "turkiye",
    "viet nam": "vietnam",
}

# Agregados regionais, demográficos e grupos de renda do Banco Mundial (não são países individuais)
AGREGADOS_REGIONAIS = {
    "africa eastern and southern",
    "africa western and central",
    "arab world",
    "caribbean small states",
    "central europe and the baltics",
    "early-demographic dividend",
    "east asia & pacific",
    "east asia & pacific (excluding high income)",
    "east asia & pacific (ida & ibrd countries)",
    "east asia & pacific (ida & ibrd)",
    "euro area",
    "europe & central asia",
    "europe & central asia (excluding high income)",
    "europe & central asia (ida & ibrd countries)",
    "europe & central asia (ida & ibrd)",
    "european union",
    "fragile and conflict affected situations",
    "heavily indebted poor countries (hipc)",
    "high income",
    "ibrd only",
    "ida & ibrd total",
    "ida blend",
    "ida only",
    "ida total",
    "late-demographic dividend",
    "latin america & caribbean",
    "latin america & caribbean (excluding high income)",
    "latin america & caribbean (ida & ibrd)",
    "latin america & the caribbean (ida & ibrd countries)",
    "least developed countries: un classification",
    "low & middle income",
    "low income",
    "lower middle income",
    "middle east & north africa",
    "middle east & north africa (excluding high income)",
    "middle east & north africa (ida & ibrd countries)",
    "middle east & north africa (ida & ibrd)",
    "middle income",
    "north america",
    "not classified",
    "oecd members",
    "other small states",
    "pacific island small states",
    "post-demographic dividend",
    "pre-demographic dividend",
    "small states",
    "south asia",
    "south asia (ida & ibrd)",
    "sub-saharan africa",
    "sub-saharan africa (excluding high income)",
    "sub-saharan africa (ida & ibrd countries)",
    "sub-saharan africa (ida & ibrd)",
    "upper middle income",
    "world",
}


def carregar():
    arquivos = sorted(ORIGEM.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"Nada encontrado em {ORIGEM}")
    caminho = arquivos[-1]

    colunas_uteis = [
        "country",
        "date",
        "GDP_current_US",
        "population",
        "inflation_annual%",
    ]
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)
    log.info("paises: lido %s %s", caminho.name, df.shape)
    return df, caminho


def converter_tipos(df):
    df = df.copy()
    # A coluna 'date' vem no formato ISO 'AAAA-MM-DD'; extrai o ano inteiro (Int64).
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.year.astype("Int64")
    for col in ["GDP_current_US", "population", "inflation_annual%"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def padronizar_pais(df):
    """Preserva o rótulo legível em 'country' e cria 'country_chave' para comparação/junção."""
    df = df.copy()
    chave = limpeza.chave_texto(df["country"])
    df["country_chave"] = limpeza.aplicar_mapa(chave, MAPA_PAISES)
    return df


def remover_agregados(df):
    mascara = df["country_chave"].isin(AGREGADOS_REGIONAIS)
    linhas_removidas = int(mascara.sum())
    entidades_removidas = int(df.loc[mascara, "country_chave"].nunique())
    log.info(
        "paises: %d linhas de agregados removidas (%d entidades)",
        linhas_removidas,
        entidades_removidas,
    )
    return df.loc[~mascara].copy(), linhas_removidas, entidades_removidas


def tratar_vazios(df):
    antes = len(df)
    df = df.dropna(subset=["country", "country_chave", "date", "GDP_current_US", "population"]).copy()
    removidos = antes - len(df)
    if removidos:
        log.warning("paises: %d linhas removidas por falta de país/ano/PIB/População", removidos)
    return df, removidos


def conferir_chave(df, chaves):
    repetidas = int(df.duplicated(subset=chaves).sum())
    if repetidas:
        log.warning("paises: %d chaves repetidas em %s removidas", repetidas, chaves)
        df = df.drop_duplicates(subset=chaves).copy()
    else:
        log.info("paises: 0 chaves repetidas em %s", chaves)
    return df, repetidas


def variacao_anual(df, chave, tempo, valor):
    df = df.sort_values([chave, tempo]).copy()
    pct = df.groupby(chave)[valor].pct_change(fill_method=None) * 100
    diff_ano = df.groupby(chave)[tempo].diff()
    # Só calcula variação anual quando o registro anterior do país é do ano imediatamente anterior
    df["variacao_pct_PIB"] = pct.where(diff_ano == 1)
    return df


def faixa_por_quartil(df, coluna, tempo, rotulos):
    """Classifica em quartis por ano para não misturar distribuições de décadas distintas."""
    df = df.copy()
    faixas = df.groupby(tempo)[coluna].transform(
        lambda s: pd.qcut(s, q=len(rotulos), labels=rotulos).astype("object")
    )
    df[coluna + "_faixa"] = pd.Categorical(faixas, categories=rotulos, ordered=True)
    return df


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "paises.parquet"
    df.to_parquet(destino, index=False)
    log.info("paises: salvo em %s %s", destino, df.shape)
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
    df = converter_tipos(df)
    df = padronizar_pais(df)
    df, linhas_agregados, entidades_agregados = remover_agregados(df)
    df, removidos_vazios = tratar_vazios(df)
    df, duplicatas = conferir_chave(df, chaves=["country_chave", "date"])

    df = faixa_por_quartil(
        df,
        coluna="population",
        tempo="date",
        rotulos=["muito pequeno", "pequeno", "grande", "muito grande"],
    )
    df = variacao_anual(df, chave="country_chave", tempo="date", valor="GDP_current_US")

    destino = salvar(df)
    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Filtro aplicado para manter colunas econômicas (country, date, GDP_current_US, population, inflation_annual%)",
            "Espaços removidos de nomes de colunas e strings",
            "Coluna 'date' convertida de ISO (AAAA-MM-DD) para ano inteiro (Int64)",
            "Rótulo legível preservado em 'country' e chave normalizada criada em 'country_chave' (chave_texto + MAPA_PAISES)",
            f"Agregados regionais e grupos de renda removidos: {linhas_agregados} linhas ({entidades_agregados} entidades)",
            f"Registros sem país, ano, PIB ou População removidos: {removidos_vazios} linhas",
            f"Duplicatas verificadas pela chave composta (country_chave, date): {duplicatas} removidas",
            "Atributo derivado criado: Faixa de população por quartil anual (population_faixa)",
            "Atributo derivado criado: Variação percentual anual consecutiva do PIB (variacao_pct_PIB, exigindo diff(date) == 1)",
        ],
    )


if __name__ == "__main__":
    configurar_log()
    main()
