import json
import logging
import shutil
from datetime import date, datetime
from pathlib import Path

import kagglehub

from config import BRONZE, configurar_log

log = logging.getLogger(__name__)

DATASET = "nicolasgonzalezmunoz/world-bank-world-development-indicators"
PASTA = BRONZE / "banco_mundial"


def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    log.info("banco_mundial: baixado em %s", pasta)
    return Path(pasta)


def localizar(pasta):
    arquivos = sorted(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado na pasta do Kaggle.")
    log.info("banco_mundial: encontrados %s", [a.name for a in arquivos])
    return arquivos[0]


def copiar(origem):
    PASTA.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = PASTA / f"world_bank_development_indicators_{hoje}.csv"
    shutil.copy(origem, destino)
    log.info("banco_mundial: copiado para %s", destino)
    return destino


def registrar(origem, destino):
    info = {
        "fonte": DATASET,
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = PASTA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    log.info("banco_mundial: proveniência atualizada em %s", caminho)
    return info


def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)


if __name__ == "__main__":
    configurar_log()
    main()
