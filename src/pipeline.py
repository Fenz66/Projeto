import logging
import subprocess
import sys
import time
from pathlib import Path

from config import RAIZ, configurar_log

log = logging.getLogger(__name__)


def _dbt():
    candidato = Path(sys.executable).parent / ("dbt.exe" if sys.platform == "win32" else "dbt")
    return str(candidato) if candidato.exists() else "dbt"


def etapa_ingestao():
    import ingerir_paises
    import ingerir_steam

    ingerir_steam.main()
    ingerir_paises.main()


def etapa_transformacao():
    import transformar_paises
    import transformar_steam

    transformar_steam.main()
    transformar_paises.main()


def etapa_carga():
    import carga

    carga.main()


def etapa_modelagem():
    subprocess.run([_dbt(), "run"], cwd=RAIZ / "ecox14", check=True)


def etapa_testes():
    subprocess.run([_dbt(), "test"], cwd=RAIZ / "ecox14", check=True)


ETAPAS = [
    ("ingestao", etapa_ingestao),
    ("transformacao", etapa_transformacao),
    ("carga", etapa_carga),
    ("modelagem", etapa_modelagem),
    ("testes", etapa_testes),
]


def executar(nome, funcao):
    inicio = time.perf_counter()
    log.info("etapa %s: inicio", nome)
    try:
        funcao()
    except Exception:
        log.exception("etapa %s falhou", nome)
        raise
    log.info("etapa %s: fim em %.1fs", nome, time.perf_counter() - inicio)


def main(a_partir_de=None):
    configurar_log()
    nomes = [nome for nome, _ in ETAPAS]

    if a_partir_de is not None and a_partir_de not in nomes:
        log.error("etapa invalida: '%s'. Opcoes: %s", a_partir_de, ", ".join(nomes))
        raise ValueError(f"Etapa invalida: {a_partir_de}")

    inicio_total = time.perf_counter()
    comecou = a_partir_de is None

    for nome, funcao in ETAPAS:
        if nome == a_partir_de:
            comecou = True
        if not comecou or funcao is None:
            log.info("etapa %s: pulada", nome)
            continue
        executar(nome, funcao)

    log.info("pipeline concluido em %.1fs", time.perf_counter() - inicio_total)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
