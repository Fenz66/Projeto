import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

import config
import carga
import ingerir_paises
import ingerir_steam
import transformar_paises
import transformar_steam


def _encontrar_dbt():
    candidato = Path(sys.executable).parent / (
        "dbt.exe" if sys.platform == "win32" else "dbt"
    )
    if candidato.exists():
        return str(candidato)
    no_path = shutil.which("dbt")
    if no_path:
        return no_path
    raise FileNotFoundError("Executável 'dbt' não encontrado no ambiente virtual nem no PATH.")


def etapa_ingerir_steam():
    ingerir_steam.main()


def etapa_ingerir_paises():
    ingerir_paises.main()


def etapa_transformar_steam():
    transformar_steam.main()


def etapa_transformar_paises():
    transformar_paises.main()


def etapa_carga():
    carga.carregar_prata(config.BANCO_DUCKDB)


def etapa_modelagem():
    dbt_bin = _encontrar_dbt()
    logging.info("Executando dbt run (%s) em %s", dbt_bin, config.DBT_DIR)
    subprocess.run(
        [dbt_bin, "run"],
        cwd=config.DBT_DIR,
        check=True,
    )


def etapa_auditoria():
    carga.conferir(config.BANCO_DUCKDB)


ETAPAS = [
    ("ingerir_steam", etapa_ingerir_steam),
    ("ingerir_paises", etapa_ingerir_paises),
    ("transformar_steam", etapa_transformar_steam),
    ("transformar_paises", etapa_transformar_paises),
    ("carga", etapa_carga),
    ("modelagem", etapa_modelagem),
    ("auditoria", etapa_auditoria),
]


def main():
    nomes = [nome for nome, _ in ETAPAS]
    inicio_idx = 0

    if len(sys.argv) > 1:
        etapa_inicial = sys.argv[1].strip().lower()
        if etapa_inicial not in nomes:
            logging.error(
                "Etapa inválida: '%s'. Etapas disponíveis: %s",
                etapa_inicial,
                ", ".join(nomes),
            )
            sys.exit(1)
        inicio_idx = nomes.index(etapa_inicial)
        logging.info("Retomando pipeline a partir da etapa: %s", etapa_inicial)

    inicio_total = time.perf_counter()
    logging.info("=== Iniciando pipeline completo (Medallion) ===")

    try:
        for nome, funcao in ETAPAS[inicio_idx:]:
            t0 = time.perf_counter()
            logging.info("--- Etapa [%s] iniciada ---", nome)
            funcao()
            duracao = time.perf_counter() - t0
            logging.info("--- Etapa [%s] concluída em %.2fs ---", nome, duracao)
    except Exception:
        logging.exception("Falha na execução do pipeline!")
        sys.exit(1)

    total = time.perf_counter() - inicio_total
    logging.info("=== Pipeline concluído com sucesso em %.2fs ===", total)


if __name__ == "__main__":
    main()
