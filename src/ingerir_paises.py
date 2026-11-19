import json
import logging
import shutil
from datetime import date, datetime
from pathlib import Path

import kagglehub

import config


def baixar():
    pasta = kagglehub.dataset_download(config.DATASET_BANCO_MUNDIAL)
    logging.info("Dataset Banco Mundial baixado em: %s", pasta)
    return Path(pasta)


def localizar(pasta):
    arquivos = sorted(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado na pasta do Kaggle.")
    logging.info("CSVs encontrados (Banco Mundial): %s", [a.name for a in arquivos])
    return arquivos[0]


def copiar(origem):
    config.BRONZE_BANCO_MUNDIAL.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = config.BRONZE_BANCO_MUNDIAL / f"world_bank_development_indicators_{hoje}.csv"
    shutil.copy(origem, destino)
    logging.info("Arquivo Banco Mundial copiado para: %s", destino)
    return destino


def registrar(origem, destino):
    info = {
        "fonte": config.DATASET_BANCO_MUNDIAL,
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = config.BRONZE_BANCO_MUNDIAL / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    logging.info("Proveniência atualizada em: %s", caminho)
    return info


def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)


if __name__ == "__main__":
    main()
