import logging

import pandas as pd
from data_profiling import ProfileReport

import config


def mais_recente(path, padrao):
    arquivos = sorted(path.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(
            f"A pasta {path} está vazia ou nenhum arquivo corresponde a {padrao}."
        )
    return arquivos[-1]


def gerar(caminho):
    df = pd.read_csv(caminho, low_memory=False)
    perfil = ProfileReport(df, title=caminho.name)
    config.RELATORIOS.mkdir(parents=True, exist_ok=True)
    saida = config.RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida


def main():
    caminho_steam = mais_recente(config.BRONZE_STEAM, config.PADRAO_STEAM)
    logging.info("Perfilando: %s", caminho_steam.name)
    saida_steam = gerar(caminho_steam)
    logging.info("Relatório salvo em: %s", saida_steam)

    caminho_mundial = mais_recente(
        config.BRONZE_BANCO_MUNDIAL, config.PADRAO_BANCO_MUNDIAL
    )
    logging.info("Perfilando: %s", caminho_mundial.name)
    saida_mundial = gerar(caminho_mundial)
    logging.info("Relatório salvo em: %s", saida_mundial)


if __name__ == "__main__":
    main()
