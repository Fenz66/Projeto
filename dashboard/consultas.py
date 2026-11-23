"""Consultas somente leitura na camada Ouro (DuckDB) para o painel Streamlit."""

from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "ouro" / "projeto.duckdb"

_SQL_FAIXA_DESC = """
select
    nome_pais,
    ano,
    faixa_populacional,
    round(pib_per_capita, 2) as pib_per_capita,
    round(avg(preco_usd), 2) as preco_medio_usd,
    round(avg(indice_acessibilidade), 2) as indice_acessibilidade,
    count(*) as qtd_jogos
from ouro.vw_acessibilidade_completa
where preco_usd > ?
  and (cast(? as double) is null or preco_usd <= cast(? as double))
  and (? = 'Todas' or faixa_populacional = ?)
group by nome_pais, ano, faixa_populacional, pib_per_capita
order by indice_acessibilidade desc
limit ?
"""

_SQL_FAIXA_ASC = """
select
    nome_pais,
    ano,
    faixa_populacional,
    round(pib_per_capita, 2) as pib_per_capita,
    round(avg(preco_usd), 2) as preco_medio_usd,
    round(avg(indice_acessibilidade), 2) as indice_acessibilidade,
    count(*) as qtd_jogos
from ouro.vw_acessibilidade_completa
where preco_usd > ?
  and (cast(? as double) is null or preco_usd <= cast(? as double))
  and (? = 'Todas' or faixa_populacional = ?)
group by nome_pais, ano, faixa_populacional, pib_per_capita
order by indice_acessibilidade asc
limit ?
"""

_SQL_JOGO_DESC = """
select
    nome_pais,
    ano,
    faixa_populacional,
    nome_jogo,
    round(preco_usd, 2) as preco_usd,
    round(pib_per_capita, 2) as pib_per_capita,
    round(indice_acessibilidade, 2) as indice_acessibilidade
from ouro.vw_acessibilidade_completa
where jogo_id = ?
  and (? = 'Todas' or faixa_populacional = ?)
order by indice_acessibilidade desc
limit ?
"""

_SQL_JOGO_ASC = """
select
    nome_pais,
    ano,
    faixa_populacional,
    nome_jogo,
    round(preco_usd, 2) as preco_usd,
    round(pib_per_capita, 2) as pib_per_capita,
    round(indice_acessibilidade, 2) as indice_acessibilidade
from ouro.vw_acessibilidade_completa
where jogo_id = ?
  and (? = 'Todas' or faixa_populacional = ?)
order by indice_acessibilidade asc
limit ?
"""


def _consultar(sql, parametros=None):
    con = duckdb.connect(str(BANCO), read_only=True)
    try:
        return con.execute(sql, parametros or []).df()
    finally:
        con.close()


def faixas_populacionais():
    """Lista ordenada dos quartis populacionais diretamente de ouro.dim_pais."""
    return _consultar(
        """
        select distinct faixa_populacional
        from ouro.dim_pais
        where faixa_populacional is not null
        order by case faixa_populacional
            when 'muito pequeno' then 1
            when 'pequeno' then 2
            when 'grande' then 3
            when 'muito grande' then 4
            else 5
        end
        """
    )


def buscar_jogos(termo="", limite=50):
    """Busca jogos pagos diretamente em ouro.dim_steam usando filtro parametrizado."""
    termo_limpo = (termo or "").strip()
    if termo_limpo:
        return _consultar(
            """
            select jogo_id, nome_jogo, preco_usd
            from ouro.dim_steam
            where preco_usd > 0
              and nome_jogo is not null
              and nome_jogo ilike ?
            order by preco_usd desc, nome_jogo
            limit ?
            """,
            ["%" + termo_limpo + "%", int(limite)],
        )
    return _consultar(
        """
        select jogo_id, nome_jogo, preco_usd
        from ouro.dim_steam
        where preco_usd > 0
          and nome_jogo is not null
          and flag_preco_extremo = false
        order by preco_usd desc, nome_jogo
        limit ?
        """,
        [int(limite)],
    )


def acessibilidade_por_faixa(faixa="Todas", preco_min=0.0, preco_max=None, ordem="desc", limite=214):
    """Agrega o índice médio de acessibilidade por país para uma faixa de preço e porte populacional."""
    sql = _SQL_FAIXA_ASC if ordem == "asc" else _SQL_FAIXA_DESC
    faixa_param = faixa or "Todas"
    preco_max_param = float(preco_max) if preco_max is not None else None
    return _consultar(
        sql,
        [float(preco_min), preco_max_param, preco_max_param, faixa_param, faixa_param, int(limite)],
    )


def acessibilidade_por_jogo(jogo_id, faixa="Todas", ordem="desc", limite=214):
    """Compara a acessibilidade de um jogo específico entre países."""
    sql = _SQL_JOGO_ASC if ordem == "asc" else _SQL_JOGO_DESC
    faixa_param = faixa or "Todas"
    return _consultar(
        sql,
        [int(jogo_id), faixa_param, faixa_param, int(limite)],
    )
