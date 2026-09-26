import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests


INDICADOR = "NY.GDP.PCAP.CD"
PERIODO = "2000:2023"
POR_PAGINA = 1000

URL = f"https://api.worldbank.org/v2/country/all/indicator/{INDICADOR}"

BRONZE = Path("dados/bronze/banco_mundial/indicador_paises")


def buscar_pagina(pagina):

    resposta = requests.get(
        URL,
        params={
            "format": "json",
            "date": PERIODO,
            "per_page": POR_PAGINA,
            "page": pagina,
        },
        timeout=60,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    return dados[0], dados[1]


def buscar_tudo():

    meta, registros = buscar_pagina(1)
    total_paginas = meta["pages"]
    print("total de registros informados:", meta["total"])
    print("paginas                      :", total_paginas)
    print("atualizado pela fonte em     :", meta.get("lastupdated"))

    for pagina in range(2, total_paginas + 1):
        print(f"  buscando pagina {pagina} de {total_paginas}")
        _, mais = buscar_pagina(pagina)
        registros.extend(mais)

    print("registros recebidos          :", len(registros))
    if len(registros) != meta["total"]:
        print("ATENCAO: recebido diferente do informado pela API.")
    return meta, registros


def salvar(registros):
    BRONZE.mkdir(parents=True, exist_ok=True)
    df = pd.json_normalize(registros)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"{INDICADOR}_{hoje}.csv"
    df.to_csv(destino, index=False)

    print()
    print("formato:", df.shape)
    print("colunas:", df.columns.tolist())
    print("salvo em:", destino)
    return destino


def registrar(destino, meta, quantidade):
    info = {
        "fonte": URL,
        "indicador": INDICADOR,
        "periodo": PERIODO,
        "arquivo_bronze": destino.name,
        "registros_informados_pela_api": meta["total"],
        "registros_recebidos": quantidade,
        "fonte_atualizada_em": meta.get("lastupdated"),
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")
    print("proveniencia:", caminho)
    return info


def main():
    meta, registros = buscar_tudo()
    destino = salvar(registros)
    registrar(destino, meta, len(registros))


if __name__ == "__main__":
    main()