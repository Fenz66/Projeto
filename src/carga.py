import logging

import duckdb

from config import OURO, PRATA, configurar_log

log = logging.getLogger(__name__)

BANCO = OURO / "projeto.duckdb"


def criar_esquemas(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS prata")
    con.execute("CREATE SCHEMA IF NOT EXISTS ouro")


def carregar_prata(con):
    caminho_paises = (PRATA / "paises.parquet").as_posix()
    caminho_steam = (PRATA / "steam.parquet").as_posix()

    con.execute(
        f"CREATE OR REPLACE TABLE prata.paises AS SELECT * FROM read_parquet('{caminho_paises}')"
    )
    con.execute(
        f"CREATE OR REPLACE TABLE prata.steam AS SELECT * FROM read_parquet('{caminho_steam}')"
    )

    n_paises = con.execute("SELECT COUNT(*) FROM prata.paises").fetchone()[0]
    n_steam = con.execute("SELECT COUNT(*) FROM prata.steam").fetchone()[0]
    log.info("carga: prata.paises=%d, prata.steam=%d", n_paises, n_steam)


def main():
    OURO.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(BANCO)) as con:
        criar_esquemas(con)
        carregar_prata(con)
    log.info("carga: banco atualizado em %s", BANCO)


if __name__ == "__main__":
    configurar_log()
    main()
