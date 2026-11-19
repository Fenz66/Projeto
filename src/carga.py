import logging

import duckdb

import config


def carregar_prata(banco_path=config.BANCO_DUCKDB):
    banco_path.parent.mkdir(parents=True, exist_ok=True)
    caminho_paises = (config.PRATA / "paises.parquet").as_posix()
    caminho_steam = (config.PRATA / "steam.parquet").as_posix()

    with duckdb.connect(str(banco_path)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS prata")
        con.execute("CREATE SCHEMA IF NOT EXISTS ouro")

        con.execute(
            f"CREATE OR REPLACE TABLE prata.paises AS SELECT * FROM read_parquet('{caminho_paises}')"
        )
        con.execute(
            f"CREATE OR REPLACE TABLE prata.steam AS SELECT * FROM read_parquet('{caminho_steam}')"
        )

        n_paises = con.execute("SELECT COUNT(*) FROM prata.paises").fetchone()[0]
        n_steam = con.execute("SELECT COUNT(*) FROM prata.steam").fetchone()[0]

    logging.info(
        "Carga Prata -> DuckDB concluída (%s): prata.paises=%d, prata.steam=%d",
        banco_path.name,
        n_paises,
        n_steam,
    )


def conferir(banco_path=config.BANCO_DUCKDB):
    with duckdb.connect(str(banco_path), read_only=True) as con:
        total_fato = con.execute(
            "SELECT COUNT(*) FROM ouro.fato_acessibilidade"
        ).fetchone()[0]
        total_view = con.execute(
            "SELECT COUNT(*) FROM ouro.vw_acessibilidade_completa"
        ).fetchone()[0]

        grao = con.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT pais_id, ano, jogo_id
                FROM ouro.fato_acessibilidade
                GROUP BY pais_id, ano, jogo_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        orfaos_pais = con.execute(
            """
            SELECT COUNT(*)
            FROM ouro.fato_acessibilidade f
            LEFT JOIN ouro.dim_pais d USING (pais_id, ano)
            WHERE d.pais_id IS NULL
            """
        ).fetchone()[0]

        orfaos_steam = con.execute(
            """
            SELECT COUNT(*)
            FROM ouro.fato_acessibilidade f
            LEFT JOIN ouro.dim_steam s USING (jogo_id)
            WHERE s.jogo_id IS NULL
            """
        ).fetchone()[0]

    logging.info(
        "Auditoria DuckDB — fato=%d | view=%d | duplicatas_grao=%d | orfaos_dim_pais=%d | orfaos_dim_steam=%d",
        total_fato,
        total_view,
        grao,
        orfaos_pais,
        orfaos_steam,
    )

    if total_fato == 0:
        raise ValueError("Erro: ouro.fato_acessibilidade está vazia.")
    if grao > 0:
        raise ValueError(
            f"Erro: {grao} duplicatas encontradas no grão (pais_id, ano, jogo_id) da tabela fato."
        )
    if orfaos_pais > 0:
        raise ValueError(
            f"Erro: {orfaos_pais} registros órfãos encontrados em relação a ouro.dim_pais."
        )
    if orfaos_steam > 0:
        raise ValueError(
            f"Erro: {orfaos_steam} registros órfãos encontrados em relação a ouro.dim_steam."
        )
    if total_view != total_fato:
        raise ValueError(
            f"Erro: divergência entre ouro.vw_acessibilidade_completa ({total_view}) e ouro.fato_acessibilidade ({total_fato})."
        )

    logging.info("Auditoria concluída: 0 duplicatas no grão e 0 registros órfãos.")


if __name__ == "__main__":
    carregar_prata()
