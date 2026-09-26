import json
import shutil
from datetime import date, datetime
from pathlib import Path

import kagglehub

DATASET = "nicolasgonzalezmunoz/world-bank-world-development-indicators"
BRONZE = Path("dados/bronze/banco_mundial")

def baixar():

    pasta = kagglehub.dataset_download(DATASET)
    print("baixado em:", pasta)
    return Path(pasta)

def localizar(pasta):
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado na pasta do Kaggle.")
    print("encontrados:", [a.name for a in arquivos])
    return arquivos[0]

def copiar(origem):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"world_bank_development_indicators_{hoje}.csv"
    shutil.copy(origem, destino)
    print("copiado para:", destino)
    return destino

def registrar(origem, destino):
    info = {
        "fonte": DATASET,
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    print("proveniencia atualizada em:", caminho)
    return info

def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)

if __name__ == "__main__":
    main()