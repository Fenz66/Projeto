from pathlib import Path
from datetime import date
import shutil
import kagglehub
import os
import json

CACHE = Path.cwd() / "Kaggle_cache"
CACHE.mkdir(parents=True, exist_ok=True)

os.environ["KAGGLEHUB_CACHE"] = str(CACHE)
os.environ["KAGGLE_KEY"] = "KGAT_ef08a24d09d95157050283e2bbc99b15"


DATASET = "rishavsvault/most-streamed-artists-on-spotify"
BRONZE = Path("dados/bronze/spotify")

def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    print("baixado em:", pasta)
    return Path(pasta)
if __name__ == "__main__":
    baixar()

def localizar(pasta):
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("nenhum CSV")
    print("encontrados:", [a.name for a in arquivos])
    return arquivos[0]

def copiar(origem):
        BRONZE.mkdir(parents=True, exist_ok=True)
        hoje = date.today.str
        destino = BRONZE / f"artists_{hoje}.csv"
        shutil.copy(origem, destino)
        return destino

def registrar(origem, destino):
        info = {
            "fonte": DATASET,
            "arquivo_origem": origem.name,
            "arquivo_destino": destino.name,
            "extraido_em": date.now()
        }

        (BRONZE / "proveniencia.json").write_text(json.dumps(info, indent=2))

def conferir(dados):
    meta = dados[0]
    print("registros:", meta["total"])

def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)

if __name__ == "__main__":
    main()