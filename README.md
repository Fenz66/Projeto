# Acessibilidade Global no Mercado de Jogos: O Impacto da Precificação Padrão (USD)

- **Disciplina:** Engenharia de Dados na Prática (ECOX14 — UNIFEI, Profa. Bárbara Pimenta Caetano)
- **Autor:** Caio Freitas Santos (Matrícula: 2025014153)
- **Pergunta norteadora:** Como o preço base (em USD) dos jogos da Steam afeta a acessibilidade de compra em diferentes países, quando cruzado com seus respectivos indicadores socioeconômicos (como PIB per capita e Paridade do Poder de Compra)?

### Adaptação de escopo
Como não há uma base pública consolidada com séries históricas de preços regionais em moedas locais na Steam nem série completa de Paridade do Poder de Compra (PPP) no dataset unificado utilizado, o projeto adota o **preço base em USD** da Steam como referência global e cruza-o com o **PIB per capita em dólares correntes (`GDP_current_US / population`)** do Banco Mundial para construir um **Índice de Acessibilidade** comparável entre países.

---

## Arquitetura (Medallion)

O fluxo de dados é estritamente unidirecional (**Bronze → Prata → Ouro**) e 100% reprodutível por código:

- **Bronze (`dados/bronze/`):** CSVs brutos e imutáveis datados (`_YYYYMMDD.csv`) extraídos via KaggleHub, acompanhados do registro acumulativo de proveniência (`proveniencia.jsonl` em modo *append*, seguindo princípios FAIR).
- **Prata (`dados/prata/`):** Dados limpos, padronizados e enriquecidos com atributos derivados, salvos em formato colunar **Parquet** (`steam.parquet` e `paises.parquet`) com log acumulativo de decisões e contagens em `dados/prata/proveniencia.jsonl`.
- **Ouro (`dados/ouro/projeto.duckdb` + `ecox14/`):** Banco analítico **DuckDB** modelado via **dbt** em esquema estrela (`dim_pais`, `dim_steam`, `fato_acessibilidade` como tabelas e `vw_acessibilidade_completa` como view), validado por auditoria automatizada de grão e integridade referencial.

---

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Steam Games Dataset (Daily Updates) | CSV | KaggleHub | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates) |
| World Bank World Development Indicators | CSV | KaggleHub | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/nicolasgonzalezmunoz/world-bank-world-development-indicators) |

---

## Defeitos conhecidos das fontes

### Steam Store (Kaggle)
- Registros de preços com valores ausentes ou texto inválido.
- Presença de valores extremos (*outliers*) muito altos que podem distorcer médias.
- Possibilidade de chaves duplicadas para o mesmo jogo (`app_id`).
- Presença de jogos gratuitos (`price = 0`), que não representam barreira financeira de compra.

### Banco Mundial (Kaggle — WDI)
- Mistura de **agregados regionais, demográficos e grupos de renda** (ex.: `World`, `Euro area`, `High income`, `OECD members`) junto aos países individuais.
- Coluna `date` formatada como texto ISO completo (`AAAA-MM-DD`, ex.: `1960-01-01`) em vez de ano inteiro.
- Nomes de colunas e textos sujeitos a espaços extras, variações de grafia e renomeações históricas (ex.: `United States` / `USA`, `Czech Republic` / `Czechia`, `Turkey` / `Turkiye`, `Viet Nam` / `Vietnam`).
- Ausência de indicadores financeiros essenciais (`GDP_current_US` ou `population`) em diversos pares país-ano.

---

## Decisões de tratamento

### Steam Store (`src/transformar_steam.py`)
- **Entrada Bronze:** `143.333` registros (`steam_games_20261014.csv`).
- **Filtro de colunas:** mantidas apenas `app_id`, `name` e `price`.
- **Limpeza de espaços:** removidos espaços extras dos nomes de colunas e colunas textuais via `src/limpeza.py`.
- **Chaves duplicadas (`app_id`):** `0` duplicatas encontradas/removidas.
- **Preços vazios ou inválidos:** `price` convertido com `pd.to_numeric(..., errors="coerce")`; removidos **`1.321`** jogos sem preço válido.
- **Valores extremos (*outliers*):** marcados **`6.750`** jogos na flag booleana `price_extremo` pelo método IQR (`Q1 - 1,5*IQR` a `Q3 + 1,5*IQR`, intervalo `[-12,51; 23,49]`), **mantendo as linhas** por se tratarem de extremos legítimos de mercado (edições especiais/pacotes caros).
- **Saída Prata (`dados/prata/steam.parquet`):** **`142.012`** registros (`113.922` jogos pagos + `28.090` jogos gratuitos).

### Banco Mundial (`src/transformar_paises.py`)
- **Entrada Bronze:** `17.272` registros (`world_bank_development_indicators_20261014.csv`, `274` entidades de 1960 a 2023).
- **Filtro de colunas:** mantidas `country`, `date`, `GDP_current_US`, `population` e `inflation_annual%`.
- **Limpeza e tipos:** espaços removidos; `date` convertida de texto ISO (`AAAA-MM-DD`) para ano inteiro (`Int64`); indicadores econômicos convertidos para numérico.
- **Padronização de nomes:** `country` normalizado em minúsculas e sem acentos (`NFKD`) e unificado via `MAPA_PAISES` (ex.: `united states` → `usa`, `czech republic` → `czechia`, `turkey` → `turkiye`, `viet nam` → `vietnam`).
- **Remoção de agregados regionais e grupos de renda (`remover_agregados`):** removidas **`3.291`** linhas correspondentes a **`54`** entidades agregadas que não representam países individuais.
- **Falta de dados essenciais (`tratar_vazios`):** removidas **`3.512`** linhas sem país, ano, PIB ou População (executado antes da checagem de unicidade para nunca descartar registros válidos em favor de registros vazios).
- **Chave composta (`country`, `date`):** verificadas **`0`** duplicatas após limpeza.
- **Saída Prata (`dados/prata/paises.parquet`):** **`10.469`** registros cobrindo **`214`** países distintos entre **1960 e 2022**.

---

## Atributos derivados

### Camada Prata
- **`variacao_pct_PIB` (`paises.parquet`):** variação percentual anual do PIB (`GDP_current_US`) por país em relação ao ano imediatamente anterior. Ordena por `(country, date)`, aplica `pct_change(fill_method=None) * 100` e exige que os registros sejam de anos consecutivos (`diff(date) == 1`), evitando variações distorcidas sobre lacunas plurianuais (`10.238` preenchidos e `231` ausentes por definição no primeiro ano de cada país ou após lacunas).
- **`population_faixa` (`paises.parquet`):** classificação populacional em quartis **calculados ano a ano** (`groupby("date")`) nas faixas `muito pequeno`, `pequeno`, `grande` e `muito grande`, evitando misturar a distribuição demográfica de décadas distintas (ex.: 1960 vs. 2022).

### Camada Ouro (`ecox14/models/fato_acessibilidade.sql`)
- **`pib_per_capita`:** PIB per capita anual em dólares correntes, calculado como `pib / populacao`.
- **`indice_acessibilidade`:** métrica proporcional que mede o peso relativo do preço de um jogo frente à renda média anual per capita do país, escalada por `100.000` para facilitar leitura e comparação:
  $$\text{indice\_acessibilidade} = \left(\frac{\text{preco\_usd}}{\text{pib\_per\_capita}}\right) \times 100.000$$
  Quanto **maior** o índice, **menos acessível** (mais caro proporcionalmente à renda média anual) é o jogo naquele país.

---

## Modelagem da Camada Ouro, Grão da Tabela Fato e Perdas no Cruzamento

Modelos construídos no schema `ouro` do DuckDB (`dados/ouro/projeto.duckdb`) via dbt (`ecox14/models/`):

| Objeto | Materialização | Linhas | Descrição |
|---|---|---:|---|
| `ouro.dim_pais` | `table` | `10.469` | Série histórica limpa por país e ano (`214` países, 1960–2022) com PIB, população, inflação, faixa populacional e variação anual do PIB. |
| `ouro.dim_steam` | `table` | `142.012` | Catálogo completo da Steam na Prata (incluindo jogos pagos e gratuitos), com preço em USD e flag de *outlier*. |
| `ouro.fato_acessibilidade` | `table` | `24.379.308` | Cruzamento analítico entre o ano econômico mais recente de cada país e todos os jogos pagos da Steam (`214 × 113.922`). |
| `ouro.vw_acessibilidade_completa` | `view` | `24.379.308` | Visão pronta para consumo analítico unindo a tabela fato às dimensões `dim_pais` e `dim_steam`. |

### Declaração explícita do grão
- **Grão de `ouro.fato_acessibilidade`:** **1 linha por combinação única de `(pais_id, ano, jogo_id)`**, representando a acessibilidade de um jogo pago específico no ano econômico mais recente disponível daquele país.

### Regras de recorte e perdas documentadas no cruzamento
1. **Recorte temporal por país (`ultimo_ano_pais`):** como os preços da Steam refletem o catálogo atual (2026), cruzar toda a série histórica de 1960–2022 com 142 mil jogos geraria ~1,5 bilhão de linhas sem sentido econômico (ex.: preço atual contra PIB de 1960). Por isso, a tabela fato seleciona o **último ano com `pib > 0` e `populacao > 0` de cada país** (`214` registros selecionados dentre os `10.469` da `dim_pais`, com último ano variando entre 2011 e 2022 conforme disponibilidade do Banco Mundial).
2. **Filtro de jogos pagos (`preco_usd > 0`):** na tabela fato são excluídos os **`28.090`** jogos gratuitos (`price = 0`), restando **`113.922`** jogos pagos, pois custo zero não caracteriza barreira de precificação em USD. A dimensão `ouro.dim_steam` permanece completa (`142.012` jogos) para análises de catálogo.
3. **Integridade de chaves (`is not null`) e auditoria:** todos os modelos filtram chaves não nulas e a etapa `auditoria` (`src/carga.py`) valida automaticamente em modo `read_only=True` que existem **0 duplicatas no grão** e **0 registros órfãos** tanto contra `ouro.dim_pais` quanto contra `ouro.dim_steam`.

---

## Como executar o pipeline do zero

### 1. Preparar ambiente virtual e dependências
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar o perfil do dbt (`~/.dbt/profiles.yml`)
Crie ou ajuste o arquivo `C:\Users\<seu_usuario>\.dbt\profiles.yml` usando barras normais (`/`) no caminho para `dados/ouro/projeto.duckdb`:
```yaml
ecox14:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: C:/caminho/para/o/projeto/dados/ouro/projeto.duckdb
      schema: ouro
      threads: 1
```

Valide a configuração do dbt:
```powershell
dbt debug --project-dir ecox14
```

### 3. Executar o pipeline completo (Bronze → Prata → Ouro → Auditoria)
A partir da raiz do repositório:
```powershell
python src/pipeline.py
```

### 4. Retomar a partir de uma etapa intermediária (opcional)
As etapas suportadas em ordem são: `ingerir_steam`, `ingerir_paises`, `transformar_steam`, `transformar_paises`, `carga`, `modelagem` e `auditoria`. Exemplos:
```powershell
# Reprocessar da Prata até a Auditoria (sem baixar novamente os CSVs do Kaggle)
python src/pipeline.py transformar_steam

# Reexecutar apenas a Camada Ouro (carga DuckDB + dbt run + auditoria)
python src/pipeline.py carga
```

### 5. Gerar relatórios exploratórios HTML (opcional)
```powershell
python src/explorar.py
```
Os perfis são salvos em `relatorios/` (ignorados no Git) e os logs de execução em `pipeline.log`.
