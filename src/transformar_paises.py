import json
import logging
from datetime import datetime

import pandas as pd

import config
import limpeza

MAPA_PAISES = {
    "united states of america": "usa",
    "united states": "usa",
    "uk": "united kingdom",
    "czech republic": "czechia",
    "turkey": "turkiye",
    "viet nam": "vietnam",
}

# Agregados regionais, demográficos e de renda oficiais do Banco Mundial (não são países individuais)
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
    arquivos = sorted(config.BRONZE_BANCO_MUNDIAL.glob(config.PADRAO_BANCO_MUNDIAL))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo do Banco Mundial encontrado em {config.BRONZE_BANCO_MUNDIAL}"
        )
    caminho = arquivos[-1]

    colunas_uteis = [
        "country",
        "date",
        "GDP_current_US",
        "population",
        "inflation_annual%",
    ]
    df = pd.read_csv(caminho, usecols=colunas_uteis, low_memory=False)
    logging.info("Lido arquivo Bronze Banco Mundial: %s %s", caminho.name, df.shape)
    return df, caminho


def converter_tipos(df):
    df = df.copy()
    # A coluna 'date' vem no formato ISO 'AAAA-MM-DD'; extrai apenas o ano inteiro (Int64).
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.year.astype("Int64")
    for col in ["GDP_current_US", "population", "inflation_annual%"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def remover_agregados(df):
    mascara_agregados = df["country"].isin(AGREGADOS_REGIONAIS)
    linhas_removidas = int(mascara_agregados.sum())
    entidades_removidas = int(df.loc[mascara_agregados, "country"].nunique())
    df_filtrado = df.loc[~mascara_agregados].copy()
    logging.info(
        "Agregados regionais/de renda removidos: %d linhas (%d entidades distintas)",
        linhas_removidas,
        entidades_removidas,
    )
    return df_filtrado, linhas_removidas, entidades_removidas


def tratar_vazios(df):
    antes = len(df)
    df = df.dropna(subset=["country", "date", "GDP_current_US", "population"]).copy()
    removidos = antes - len(df)
    logging.info("Linhas removidas por falta de país/ano/PIB/População: %d", removidos)
    return df, removidos


def conferir_chave(df, chaves):
    repetidas = int(df.duplicated(subset=chaves).sum())
    logging.info("Chaves repetidas na combinação %s: %d", chaves, repetidas)
    if repetidas:
        df = df.drop_duplicates(subset=chaves).copy()
    return df, repetidas


def variacao_anual(df, chave, tempo, valor):
    df = df.sort_values([chave, tempo]).copy()
    pct = df.groupby(chave)[valor].pct_change(fill_method=None) * 100
    diff_ano = df.groupby(chave)[tempo].diff()
    # Só preenche a variação anual quando o registro anterior do mesmo país é do ano consecutivo
    df["variacao_pct_PIB"] = pct.where(diff_ano == 1)
    return df


def _quartis_grupo(serie, rotulos):
    if serie.notna().sum() < len(rotulos):
        return pd.Series(pd.NA, index=serie.index, dtype="object")
    try:
        return pd.qcut(serie, q=len(rotulos), labels=rotulos).astype("object")
    except ValueError:
        return pd.qcut(
            serie.rank(method="first"), q=len(rotulos), labels=rotulos
        ).astype("object")


def faixa_por_quartil(df, coluna, tempo, rotulos):
    df = df.copy()
    nova_coluna = coluna + "_faixa"
    faixas = df.groupby(tempo, group_keys=False)[coluna].apply(
        lambda s: _quartis_grupo(s, rotulos)
    )
    df[nova_coluna] = pd.Categorical(faixas, categories=rotulos, ordered=True)
    return df


def salvar(df):
    config.PRATA.mkdir(parents=True, exist_ok=True)
    destino = config.PRATA / "paises.parquet"
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
    df = converter_tipos(df)

    if "country" in df.columns:
        df["country"] = limpeza.chave_texto(df["country"])
        df["country"] = limpeza.aplicar_mapa(df["country"], MAPA_PAISES)

    df, linhas_agregados, entidades_agregados = remover_agregados(df)
    df, removidos_vazios = tratar_vazios(df)
    df, duplicatas = conferir_chave(df, chaves=["country", "date"])

    df = faixa_por_quartil(
        df,
        coluna="population",
        tempo="date",
        rotulos=["muito pequeno", "pequeno", "grande", "muito grande"],
    )
    df = variacao_anual(df, chave="country", tempo="date", valor="GDP_current_US")

    destino = salvar(df)
    registrar(
        origem,
        destino,
        antes,
        len(df),
        [
            "Filtro aplicado para manter apenas colunas econômicas (country, date, GDP_current_US, population, inflation_annual%)",
            "Espaços removidos dos nomes de colunas e strings",
            "Coluna 'date' convertida de ISO (AAAA-MM-DD) para ano inteiro (Int64)",
            "Nomes dos países padronizados (minúsculas, sem acento) e mapeados via dicionário de sinônimos",
            f"Agregados regionais e grupos de renda removidos: {linhas_agregados} linhas ({entidades_agregados} entidades)",
            f"Registros sem país, ano, PIB ou População removidos: {removidos_vazios} linhas",
            f"Duplicatas verificadas pela chave composta (country, date): {duplicatas} removidas",
            "Atributo derivado criado: Faixa de população por quartil anual (population_faixa)",
            "Atributo derivado criado: Variação percentual anual consecutiva do PIB (variacao_pct_PIB, exigindo diff(ano) == 1)",
        ],
    )
    logging.info("Transformação do Banco Mundial concluída!")


if __name__ == "__main__":
    main()
