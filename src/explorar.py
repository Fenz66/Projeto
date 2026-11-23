import logging

import pandas as pd
from data_profiling import ProfileReport

from config import BRONZE, RELATORIOS, configurar_log

log = logging.getLogger(__name__)

FONTES = [
    (BRONZE / "steam", "steam_games_*.csv"),
    (BRONZE / "banco_mundial", "world_bank_development_indicators_*.csv"),
]


def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"Nada encontrado em {path} com padrão {padrao}.")
    return arquivos[-1]


def gerar(caminho):
    df = pd.read_csv(caminho, low_memory=False)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(parents=True, exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida


def main():
    for pasta, padrao in FONTES:
        caminho = mais_recente(pasta, padrao)
        log.info("perfilando: %s", caminho.name)
        saida = gerar(caminho)
        log.info("salvo em: %s", saida)


if __name__ == "__main__":
    configurar_log()
    main()
