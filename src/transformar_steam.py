import json
from datetime import datetime
from pathlib import Path
import pandas as pd

BRONZE = Path("dados/bronze/steam")
PRATA = Path("dados/prata")
PADRAO = "steam_games*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    
    # DICA: Olhe o terminal após rodar, ele vai listar as colunas disponíveis!
    # Isso vai te ajudar a preencher as funções abaixo durante a aula.
    print("\n--- COLUNAS DISPONÍVEIS ---")
    print(df.columns.tolist())
    print("---------------------------\n")
    
    print(df.isna().sum())
    return df, caminho

def tirar_espacos(df):
    # 1. Limpa os espaços dos NOMES das colunas (essa linha estava no seu original)
    df.columns = df.columns.str.strip()
    
    # 2. Seleciona apenas as colunas que contêm texto (evita o erro da imagem no int64)
    colunas_texto = df.select_dtypes(include=['object', 'string']).columns
    
    # 3. Aplica o strip apenas nessas colunas de texto
    for coluna in colunas_texto:
        df[coluna] = df[coluna].str.strip()
        
    return df

def separar_agregados(df):
    # TODO: MANUAL - Adaptar para a Steam
    # O que procurar na aula: O professor deve substituir "region.value" (que era 
    # de um dataset de países) por alguma coluna de filtro de jogos da Steam.
    # Por enquanto, comentei a lógica original para não dar KeyError e o script rodar.
    
    # e_pais = df["region.value"] != "Aggregates"
    # print("paises :", e_pais.sum())
    # print("agregados:", (~e_pais).sum())
    # return df[e_pais].copy()
    
    return df # Retorna o dataframe sem filtrar nada por enquanto.

def conferir_chave(df, chave="id"):
    # TODO: MANUAL - Mudar o nome da chave "id"
    # O que procurar na aula: A Steam provavelmente usa "AppID" ou "appid". 
    # Quando o professor chegar aqui, basta trocar a palavra "id" (na linha def acima).
    
    repetidas = df[chave].duplicated().sum()
    print("chaves repetidas:", repetidas)
    if repetidas:
        print(df[df[chave].duplicated(keep=False)])
    return df.drop_duplicates(subset=chave)

def converter_tipos(df):
    # TODO: MANUAL - Adaptar para a Steam
    # O que procurar na aula: O professor deve apagar "longitude" e "latitude" 
    # e colocar as colunas numéricas da Steam que precisam de conversão (ex: Preço).
    # Comentei para o código não travar com KeyError.
    
    # for coluna in ["longitude", "latitude"]:
    #     df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    
    return df # Retorna o dataframe sem converter nada por enquanto.

def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (
    (df[coluna] < baixo) | (df[coluna] > alto))
    print(coluna, df[coluna + "_extremo"].sum())
    return df

def marcar_zscore(df, coluna, limite=3):
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_z"] = z.abs() > limite
    print(coluna, "z acima de", limite, ":",
    df[coluna + "_z"].sum())
    return df

def remover_erros(df, coluna, minimo, maximo):
    valido = df[coluna].between(minimo, maximo)
    print("removidas:", (~valido).sum())
    return df[valido].copy()

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    # TODO: MANUAL - Mudar nome do arquivo salvo.
    # O professor provavelmente vai mudar "paises.parquet" para "steam.parquet".
    destino = PRATA / "paises.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
    "origem": origem.name,
    "arquivo_prata": destino.name,
    "linhas_antes": antes,
    "linhas_depois": depois,
    "decisoes": decisoes,
    "transformado_em": datetime.now().isoformat(
    timespec="seconds"),
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")

def main():
    df, origem = carregar()
    antes = len(df)
    
    df = tirar_espacos(df)
    df = separar_agregados(df)
    
    # ATENÇÃO: Se o professor passar a chave aqui na chamada, preste atenção!
    # Ex: df = conferir_chave(df, chave="AppID")
    df = conferir_chave(df) 
    
    df = converter_tipos(df)
    
    destino = salvar(df)
    
    # O professor também deve mudar as "decisões" abaixo mais pra frente na aula.
    registrar(origem, destino, antes, len(df), [
    "espacos removidos",
    "agregados separados",
    "longitude e latitude convertidas",
    ])

if __name__ == "__main__":
    main()

'''
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

BRONZE = Path("dados/bronze/steam")
PRATA = Path("dados/prata")
PADRAO = "steam_games*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    print(df.columns.tolist())
    print(df.isna().sum())
    return df, caminho


#def tirar_espacos(df):
#    df.columns = df.columns.str.strip()
#    for coluna in df.select_dtypes(include="object"):
#        df[coluna] = df[coluna].str.strip()
#    return df

def tirar_espacos(df):
    # Seleciona apenas as colunas que contêm texto (strings/objetos)
    colunas_texto = df.select_dtypes(include=['object', 'string']).columns
    
    # Aplica o strip apenas nessas colunas
    for coluna in colunas_texto:
        df[coluna] = df[coluna].str.strip()
        
    return df

def separar_agregados(df):
    e_pais = df["region.value"] != "Aggregates"
    print("paises :", e_pais.sum())
    print("agregados:", (~e_pais).sum())
    return df[e_pais].copy()

def conferir_chave(df, chave="id"):
    repetidas = df[chave].duplicated().sum()
    print("chaves repetidas:", repetidas)
    if repetidas:
        print(df[df[chave].duplicated(keep=False)])
    return df.drop_duplicates(subset=chave)

def converter_tipos(df):
    for coluna in ["longitude", "latitude"]:
        df[coluna] = pd.to_numeric(
        df[coluna], errors="coerce")
    return df

def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (
    (df[coluna] < baixo) | (df[coluna] > alto))
    print(coluna, df[coluna + "_extremo"].sum())
    return df

def marcar_zscore(df, coluna, limite=3):
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_z"] = z.abs() > limite
    print(coluna, "z acima de", limite, ":",
    df[coluna + "_z"].sum())
    return df

def remover_erros(df, coluna, minimo, maximo):
    valido = df[coluna].between(minimo, maximo)
    print("removidas:", (~valido).sum())
    return df[valido].copy()

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "paises.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
    "origem": origem.name,
    "arquivo_prata": destino.name,
    "linhas_antes": antes,
    "linhas_depois": depois,
    "decisoes": decisoes,
    "transformado_em": datetime.now().isoformat(
    timespec="seconds"),
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")

def main():
    df, origem = carregar()
    antes = len(df)
    df = tirar_espacos(df)
    df = separar_agregados(df)
    df = conferir_chave(df)
    df = converter_tipos(df)
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
    "espacos removidos",
    "agregados separados",
    "longitude e latitude convertidas",
    ])

if __name__ == "__main__":
    main()
'''