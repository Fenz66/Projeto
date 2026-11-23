# Acessibilidade Global no Mercado de Jogos: O Impacto da Precificação Padrão (USD)

- **Disciplina:** Engenharia de Dados na Prática (ECOX14 — UNIFEI, Profa. Bárbara Pimenta Caetano)
- **Autor:** Caio Freitas Santos (Matrícula: 2025014153)
- **Pergunta norteadora:** Como o preço base (em USD) dos jogos da Steam afeta a acessibilidade de compra em diferentes países, quando cruzado com seus respectivos indicadores socioeconômicos (como PIB per capita e Paridade do Poder de Compra)?

### Adaptação de escopo
Como não há uma base pública consolidada com séries históricas de preços regionais em moedas locais na Steam nem série completa de Paridade do Poder de Compra (PPP) no dataset unificado utilizado, o projeto adota o **preço base em USD** da Steam como referência global e cruza-o com o **PIB per capita em dólares correntes (`pib / populacao`)** do Banco Mundial para construir um **Índice de Acessibilidade** comparável entre países.

---

## Arquitetura (Medallion + Consumo)

O fluxo é estritamente unidirecional (**Bronze → Prata → Ouro → Dashboard**) e 100% reprodutível por código:

- **Bronze (`dados/bronze/`):** CSVs brutos e imutáveis datados (`_YYYYMMDD.csv`) extraídos via KaggleHub, acompanhados do registro acumulativo de proveniência (`proveniencia.jsonl` em modo *append*, Princípios FAIR — R1.2).
- **Prata (`dados/prata/`):** Dados limpos, padronizados e enriquecidos com atributos derivados, salvos em formato colunar **Parquet** (`steam.parquet` e `paises.parquet`) com log acumulativo de decisões em `dados/prata/proveniencia.jsonl`.
- **Ouro (`dados/ouro/projeto.duckdb` + `ecox14/`):** Banco analítico **DuckDB** modelado via **dbt** em esquema estrela (`dim_pais`, `dim_steam`, `fato_acessibilidade` como tabelas e `vw_acessibilidade_completa` como view), validado por **24 testes automatizados** (`dbt test`) e documentado em `ecox14/models/schema.yml` (`dbt docs`).
- **Consumo (`dashboard/`):** Painel interativo em **Streamlit** (`dashboard/painel.py` + `dashboard/consultas.py`) conectado ao DuckDB em modo somente leitura (`read_only=True`), mantendo o SQL estático, parametrizado (`?`) e isolado da interface.

---

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Steam Games Dataset (Daily Updates) | CSV | KaggleHub | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates) |
| World Bank World Development Indicators | CSV | KaggleHub | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/nicolasgonzalezmunoz/world-bank-world-development-indicators) |

### Chaves primárias das fontes
- **Steam Store (`steam.parquet`):** `app_id` (identificador único do jogo na Steam).
- **Banco Mundial (`paises.parquet`):** chave composta `(country_chave, date)` — uma linha por país e ano na série histórica da Prata (`1960–2022`).

---

## Defeitos conhecidos das fontes

### Steam Store (Kaggle)
- Registros de preços com valores ausentes ou texto inválido.
- Registros sem título (`name` nulo ou vazio).
- Presença de valores extremos (*outliers*) muito altos que podem distorcer médias.
- Possibilidade de chaves duplicadas para o mesmo jogo (`app_id`).
- Presença de jogos gratuitos (`price = 0`), que não representam barreira financeira de compra.

### Banco Mundial (Kaggle — WDI)
- Mistura de **agregados regionais, demográficos e grupos de renda** (ex.: `World`, `Euro area`, `High income`, `OECD members`) junto aos países individuais.
- Coluna `date` formatada como texto ISO completo (`AAAA-MM-DD`, ex.: `1960-01-01`) em vez de ano inteiro.
- Espaços extras em nomes de colunas e textos, além de variações/renomeações históricas de países (ex.: `United States` / `USA`, `Czech Republic` / `Czechia`, `Turkey` / `Turkiye`, `Viet Nam` / `Vietnam`).
- Ausência de indicadores financeiros essenciais (`GDP_current_US` ou `population`) em diversos pares país-ano.

---

## Decisões de tratamento

### Steam Store (`src/transformar_steam.py`)
- **Entrada Bronze:** `143.333` registros (`steam_games_20261014.csv`).
- **Filtro de colunas:** mantidas `app_id`, `name` e `price`.
- **Limpeza de espaços:** removidos espaços extras de nomes de colunas e strings via `src/limpeza.py`.
- **Unicidade (`app_id`):** `0` duplicatas encontradas/removidas.
- **Preços vazios ou inválidos:** `price` convertido com `pd.to_numeric(..., errors="coerce")`; removidos **`1.321`** jogos sem preço válido.
- **Nomes ausentes ou vazios (`tratar_nomes`):** removidos **`2`** jogos sem título válido (`1` gratuito e `1` pago). Motivo: impede exibição consistente do catálogo e do painel sem identificador legível.
- **Valores extremos (*outliers*):** marcados **`6.750`** jogos em `price_extremo` pelo método IQR (`Q1 - 1,5*IQR` a `Q3 + 1,5*IQR`, intervalo `[-12,51; 23,49]`), **mantendo as linhas** por serem extremos legítimos de mercado.
- **Saída Prata (`dados/prata/steam.parquet`):** **`142.010`** registros (`113.921` jogos pagos + `28.089` jogos gratuitos).

### Banco Mundial (`src/transformar_paises.py`)
- **Entrada Bronze:** `17.272` registros (`world_bank_development_indicators_20261014.csv`, `274` entidades de 1960 a 2023).
- **Filtro de colunas:** mantidas `country`, `date`, `GDP_current_US`, `population` e `inflation_annual%`.
- **Limpeza e tipos:** espaços removidos; `date` convertida de texto ISO (`AAAA-MM-DD`) para ano inteiro (`Int64`); indicadores econômicos convertidos para numérico.
- **Preservação do rótulo e criação de chave (`padronizar_pais`):** o nome legível do país permanece em `country` (ex.: `Brazil`, `United States`) para exibição, enquanto `country_chave` recebe `chave_texto()` + `MAPA_PAISES` para comparação e junção.
- **Remoção de agregados regionais e grupos de renda (`remover_agregados`):** removidas **`3.291`** linhas correspondentes a **`54`** entidades agregadas. Motivo: granularidade diferente da dos países individuais.
- **Falta de dados essenciais (`tratar_vazios`):** removidas **`3.512`** linhas sem país, ano, PIB ou População (executado antes da checagem de unicidade para nunca manter registros vazios em caso de sinônimos).
- **Unicidade (`country_chave`, `date`):** `0` duplicatas encontradas após limpeza.
- **Saída Prata (`dados/prata/paises.parquet`):** **`10.469`** registros cobrindo **`214`** países distintos entre **1960 e 2022**.

---

## Atributos derivados

### Camada Prata
- **`variacao_pct_PIB` (`paises.parquet`):** variação percentual anual do PIB (`GDP_current_US`) por país em relação ao ano imediatamente anterior. Ordena por `(country_chave, date)`, aplica `pct_change(fill_method=None) * 100` e exige anos consecutivos (`diff(date) == 1`). Ausente no primeiro ano de cada país ou após lacunas (`10.238` preenchidos e `231` ausentes).
- **`population_faixa` (`paises.parquet`):** agrupamento populacional em quartis **calculados por ano** (`groupby("date")`) nas faixas `muito pequeno`, `pequeno`, `grande` e `muito grande`, evitando misturar distribuições de décadas distintas.

### Camada Ouro (`ecox14/models/fato_acessibilidade.sql`)
- **`pib_per_capita`:** PIB per capita anual em dólares correntes (`pib / populacao`).
- **`indice_acessibilidade`:** atributo que só existe após o cruzamento das duas fontes, medindo o peso relativo do preço do jogo sobre o PIB per capita do país, escalado por `100.000`:
  $$\text{indice\_acessibilidade} = \left(\frac{\text{preco\_usd}}{\text{pib\_per\_capita}}\right) \times 100.000$$
  Quanto **maior** o índice, **menos acessível** é o jogo naquele país.

---

## Junção / Cruzamento

Como o dataset unificado do Banco Mundial (Kaggle) já concentra país, ano, PIB, população e inflação em uma única tabela e a base da Steam não possui coluna de país, o cruzamento entre jogos e países é um produto cartesiano (`CROSS JOIN`) de **24,3 milhões de linhas**. Seguindo a diretriz de **deixar o banco fazer junções que não cabem confortavelmente na memória em pandas**, o cruzamento não é materializado em Parquet na Prata, sendo executado diretamente no **DuckDB via dbt** na Camada Ouro.

### Quem ficou de fora no cruzamento (perdas documentadas)
- **Anos históricos anteriores em `paises.parquet` (`10.255` linhas):** a série completa `1960–2022` (`10.469` linhas) permanece intacta em `dados/prata/paises.parquet` e `prata.paises`, mas `ouro.dim_pais` seleciona apenas o **último ano com PIB e população válidos (`> 0`) por país** (**`214`** linhas, com ano de referência entre `2011` e `2022`), evitando cruzar preços atuais da Steam (2026) contra PIBs de décadas passadas (como 1960) e evitando explosão cartesiana para ~1,5 bilhão de linhas.
- **Jogos gratuitos na Steam (`28.089` linhas):** permanecem na dimensão `ouro.dim_steam` (`142.010` jogos) para análises de catálogo, mas são excluídos de `ouro.fato_acessibilidade` (`preco_usd > 0`, restando **`113.921`** jogos pagos), pois custo zero não reflete barreira de precificação em USD.

---

## Modelagem da Camada Ouro e Grão da Tabela Fato

Esquema estrela construído em `dados/ouro/projeto.duckdb` (schema `ouro`) via dbt (`ecox14/models/`):

| Objeto | Materialização | Linhas | Descrição |
|---|---|---:|---|
| `ouro.dim_pais` | `table` | `214` | **Uma linha por país** (último ano válido com PIB e população `> 0`), com `pais_id`, `nome_pais`, `ano_referencia`, `pib`, `populacao`, `inflacao_anual`, `faixa_populacional` e `variacao_pib`. |
| `ouro.dim_steam` | `table` | `142.010` | Catálogo completo da Steam na Prata (pagos e gratuitos), com `jogo_id`, `nome_jogo`, `preco_usd` e `flag_preco_extremo`. |
| `ouro.fato_acessibilidade` | `table` | `24.379.094` | Cruzamento analítico entre os `214` países e os `113.921` jogos pagos da Steam (`214 × 113.921`). |
| `ouro.vw_acessibilidade_completa` | `view` | `24.379.094` | View de consumo unindo `fato_acessibilidade` a `dim_pais` (`using (pais_id)`) e `dim_steam` (`using (jogo_id)`). |

### Declaração explícita do grão
> **Uma linha de `ouro.fato_acessibilidade` representa um jogo pago da Steam avaliado em um país no seu ano econômico mais recente: grão `(pais_id, ano, jogo_id)`.**

### Testes automatizados e documentação (dbt)
- **Testes declarativos (`ecox14/models/schema.yml`):** `unique` e `not_null` nas chaves primárias de `dim_pais` (`pais_id`) e `dim_steam` (`jogo_id`), `not_null` em `dim_steam.nome_jogo`, `accepted_values` em `dim_pais.faixa_populacional`, `not_null` nas métricas da fato e `relationships` garantindo integridade referencial de `fato_acessibilidade.pais_id -> dim_pais.pais_id` e `fato_acessibilidade.jogo_id -> dim_steam.jogo_id`.
- **Teste singular (`ecox14/tests/grao_fato_acessibilidade.sql`):** comprova que existem **0 duplicatas** na chave composta `(pais_id, ano, jogo_id)`.

---

## Governança e LGPD

- **Dados pessoais:** o projeto utiliza exclusivamente bases públicas e agregadas (catálogo público de jogos e indicadores macroeconômicos nacionais). **Nenhum dado pessoal identificável** é coletado ou processado, atendendo integralmente à LGPD por decisão de projeto.
- **Rastreabilidade (FAIR):** todas as extrações da Bronze e transformações da Prata são registradas de forma acumulativa nos arquivos `proveniencia.jsonl` (versionados no Git), e o painel exibe no rodapé a origem, a data de extração e a contagem de registros apresentados.

---

## Como executar do zero

### 1. Preparar ambiente virtual e dependências
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar o perfil do dbt (`~/.dbt/profiles.yml`)
Configure `C:\Users\<seu_usuario>\.dbt\profiles.yml` com barras normais (`/`) apontando para `dados/ouro/projeto.duckdb`:
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
Valide a conexão:
```powershell
dbt debug --project-dir ecox14
```

### 3. Executar o pipeline completo (ou retomar de uma etapa)
As etapas do pipeline são: `ingestao`, `transformacao`, `carga`, `modelagem` (`dbt run`) e `testes` (`dbt test`).
```powershell
# Pipeline completo (Bronze -> Prata -> Ouro -> Testes)
python src/pipeline.py

# Retomar a partir da Prata (sem baixar novamente os CSVs do Kaggle)
python src/pipeline.py transformacao

# Retomar a partir da Carga no DuckDB
python src/pipeline.py carga
```

### 4. Testes, documentação do dbt e painel Streamlit
```powershell
# Rodar os 24 testes do dbt isoladamente
dbt test --project-dir ecox14

# Gerar e abrir a documentação navegável (com grafo de linhagem)
dbt docs generate --project-dir ecox14
dbt docs serve --project-dir ecox14

# Abrir o painel interativo (somente leitura)
streamlit run dashboard/painel.py

# Gerar relatórios exploratórios HTML da Bronze (opcional)
python src/explorar.py
```
Os logs do pipeline são gravados em `pipeline.log` e os perfis HTML em `relatorios/` (ambos ignorados no Git).
