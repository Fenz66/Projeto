# Acessibilidade Global no Mercado de Jogos: O Impacto da Precificação Padrão (USD)

Pipeline de dados construído ao longo da disciplina **ECOX14 — Engenharia de Dados na Prática** (UNIFEI, Profa. Bárbara Pimenta Caetano). Cada pasta corresponde a uma etapa vista em aula: ingestão, exploração, tratamento, carga, modelagem declarativa, testes e apresentação.

O pipeline coleta dados públicos de jogos digitais e indicadores socioeconômicos, organiza o fluxo em três camadas (**Bronze**, **Prata** e **Ouro**) e entrega um modelo dimensional em DuckDB consultado por um painel interativo em Streamlit.

- **Autor:** Caio Freitas Santos (Matrícula: 2025014153)
- **Pergunta norteadora:** *Como o preço base (em USD) dos jogos da Steam afeta a acessibilidade de compra em diferentes países, quando cruzado com seus respectivos indicadores socioeconômicos (como PIB per capita e Paridade do Poder de Compra)?*

**Adaptação de escopo:** como não há base pública consolidada com séries históricas de preços regionais em moedas locais na Steam nem série completa de Paridade do Poder de Compra (PPP) no conjunto unificado utilizado, o projeto adota o **preço base em USD** da Steam como referência global e o cruza com o **PIB per capita em dólares correntes (`pib / populacao`)** do Banco Mundial para construir um **Índice de Acessibilidade** comparável entre países.

---

## Como rodar, do zero

Testado com **Python 3.13**, no Windows. Todos os comandos abaixo partem da raiz do repositório.

### 1. Ambiente virtual e dependências

```powershell
git clone <endereco-do-repositorio>
cd <pasta-do-repositorio>
python -m venv .venv
```

Ative o ambiente:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

Se o PowerShell recusar o script de ativação, rode antes:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Instale as dependências:

```powershell
pip install -r requirements.txt
```

O ambiente precisa estar ativado durante toda a execução para que os comandos `python`, `dbt` e `streamlit` utilizem as bibliotecas do `.venv`.

### 2. Perfil do dbt

Não há nada a configurar manualmente. O projeto traz `ecox14/profiles.yml` com caminho relativo (`../dados/ouro/projeto.duckdb`), que tem precedência sobre `~/.dbt/profiles.yml` quando o dbt é executado a partir da pasta `ecox14/` (inclusive pelo `src/pipeline.py`, que já usa `cwd=ecox14`).

Valide a conexão antes de rodar o pipeline:

```powershell
cd ecox14
dbt debug
cd ..
```

### 3. Credencial do Kaggle

As duas fontes do projeto são conjuntos públicos no Kaggle. Na versão testada do `kagglehub` (`1.0.2`), o download funcionou sem necessidade de credencial.

Se o Kaggle passar a exigir autenticação, gere um token em `kaggle.com` (*Settings → API*). O `kagglehub` aceita o token na variável de ambiente `KAGGLE_API_TOKEN` ou no arquivo `~/.kaggle/kaggle.json`:

```powershell
# Windows (PowerShell)
$env:KAGGLE_API_TOKEN = "seu-token"
```

O `.gitignore` exclui `.env` e `kaggle.json`. Nunca versione credenciais no repositório.

### 4. Execução do pipeline

```powershell
python src/pipeline.py                  # todas as etapas (Bronze -> Prata -> Ouro -> Testes)
python src/pipeline.py transformacao    # retoma a partir da Prata (sem baixar ~1 GB novamente)
python src/pipeline.py carga            # retoma a partir da carga no DuckDB
```

As etapas, em ordem, são: `ingestao`, `transformacao`, `carga`, `modelagem` (`dbt run`) e `testes` (`dbt test`). Passar um nome inválido faz o pipeline registrar o erro com a lista de etapas válidas e interromper sem executar nada indevidamente.

O log da execução vai para o terminal e para `pipeline.log`, na raiz (arquivo ignorado no Git). O histórico acumulativo do que cada extração e transformação produziu fica nos arquivos `proveniencia.jsonl`.

### 5. Testes, documentação, exploração e painel

```powershell
# Rodar os 24 testes e gerar/abrir a documentação do dbt (a partir de ecox14/)
cd ecox14
dbt test
dbt docs generate
dbt docs serve
cd ..

# Abrir o painel interativo (somente leitura, a partir da raiz)
streamlit run dashboard/painel.py

# Gerar relatórios exploratórios HTML da Bronze (opcional, fora do pipeline)
python src/explorar.py
```

---

## Estrutura do projeto

```text
.
├── src/                        pipeline em Python
│   ├── pipeline.py             ponto de entrada: roda as etapas em ordem ou retoma do meio
│   ├── config.py               caminhos-base e configuração do logging
│   ├── ingerir_steam.py        Bronze: catálogo de jogos da Steam via kagglehub
│   ├── ingerir_paises.py       Bronze: indicadores do Banco Mundial via kagglehub
│   ├── transformar_steam.py    Prata: dados/prata/steam.parquet
│   ├── transformar_paises.py   Prata: dados/prata/paises.parquet
│   ├── carga.py                copia os Parquets da Prata para o DuckDB
│   ├── limpeza.py              funções genéricas de limpeza de texto
│   └── explorar.py             perfis HTML exploratórios da Bronze, fora do pipeline
├── ecox14/                     projeto dbt: camada Ouro
│   ├── dbt_project.yml         configuração do projeto dbt (+materialized: table)
│   ├── profiles.yml            conexão local do dbt com caminho relativo para o DuckDB
│   ├── models/
│   │   ├── sources.yml         tabelas da Prata lidas pelo dbt
│   │   ├── schema.yml          documentação e testes declarativos dos modelos e colunas
│   │   ├── dim_pais.sql        dimensão de países (1 linha por país)
│   │   ├── dim_steam.sql       dimensão do catálogo de jogos da Steam
│   │   ├── fato_acessibilidade.sql      fato com índice de acessibilidade
│   │   └── vw_acessibilidade_completa.sql  view de consumo unindo fato e dimensões
│   └── tests/
│       └── grao_fato_acessibilidade.sql    teste singular do grão composto da fato
├── dashboard/                  painel consumidor em Streamlit
│   ├── painel.py               interface e gráficos (zero SQL)
│   └── consultas.py            consultas SQL parametrizadas (?), somente leitura
├── dados/                      gerado pelo pipeline (arquivos de dados não versionados)
│   ├── bronze/                 CSVs datados + proveniencia.jsonl (versionado)
│   ├── prata/                  Parquets + proveniencia.jsonl (versionado)
│   └── ouro/                   projeto.duckdb (não versionado)
├── relatorios/                 perfis HTML gerados por explorar.py (não versionado)
├── pipeline.log                log da última execução do pipeline (não versionado)
├── .gitignore
├── requirements.txt
└── README.md
```

Os arquivos `.gitkeep` mantêm a estrutura de pastas visível no GitHub mesmo sem os arquivos pesados de dados. Todos os caminhos-base do pipeline são calculados a partir de `src/config.py`, evitando caminhos absolutos dependentes de máquina.

**Por que `dashboard/` fica fora de `src/`:** tudo que está em `src/` produz dado — lê fontes externas, aplica transformações e escreve arquivos ou tabelas no banco. O painel em `dashboard/` apenas **consome** a camada Ouro em modo somente leitura (`read_only=True`) e é executado por outro processo (`streamlit`). Ele não importa nenhum módulo de `src/`: `dashboard/consultas.py` calcula a raiz do projeto por conta própria. Separar as pastas deixa claro que o painel é cliente do pipeline, e não uma etapa dele.

---

## As camadas

| Camada | Onde mora | Formato | Quem escreve |
|---|---|---|---|
| **Bronze** | `dados/bronze/<origem>/` | CSV intacto com data no nome (`_YYYYMMDD.csv`) | `ingerir_*.py` |
| **Prata** | `dados/prata/` | Parquet tipado (`steam.parquet`, `paises.parquet`) | `transformar_*.py` |
| **Ouro** | `dados/ouro/projeto.duckdb` (schema `ouro`) | Tabelas e view analíticas no DuckDB | `dbt` (`ecox14/`) |

Os arquivos de dados (`.csv`, `.parquet`, `.duckdb`, `.wal`) não são versionados no GitHub, pois o código reconstrói tudo a partir das fontes. As exceções no `.gitignore` são os arquivos `.gitkeep` e os registros acumulativos `proveniencia.jsonl` da Bronze e da Prata (Princípios FAIR — R1.2).

### Bronze
Preserva os arquivos exatamente como as fontes entregaram, sem edição nem conversão de tipo. Cada extração gera um novo CSV datado (`steam_games_20261014.csv`, `world_bank_development_indicators_20261014.csv`) e acrescenta uma linha (modo *append*, UTF-8) no `proveniencia.jsonl` da respectiva pasta, registrando fonte, arquivo de origem, arquivo salvo e data/hora da coleta. As etapas seguintes sempre leem o arquivo mais recente de cada fonte.

### Prata
Entrega dados limpos, tipados, com granularidade conferida e atributos derivados calculados em código. Cada execução grava uma linha em `dados/prata/proveniencia.jsonl` com arquivo de origem, destino, contagens de linhas antes e depois, lista de decisões aplicadas e timestamp.

| Arquivo | O que o tratamento faz |
|---|---|
| `steam.parquet` | Mantém `app_id`, `name` e `price`. Remove espaços extras via `limpeza.py`. Confere unicidade em `app_id`. Converte `price` para numérico removendo valores vazios/inválidos. Remove registros sem título (`name`). Marca outliers de preço via IQR na coluna booleana `price_extremo`, sem removê-los. |
| `paises.parquet` | Mantém `country`, `date`, `GDP_current_US`, `population` e `inflation_annual%`. Converte `date` de texto ISO (`AAAA-MM-DD`) para ano inteiro (`Int64`). Preserva o nome legível em `country` e cria `country_chave` normalizada (`chave_texto` + `MAPA_PAISES`). Remove 54 agregados regionais/grupos de renda. Descarta linhas sem dados essenciais, confere unicidade em `(country_chave, date)` e cria `variacao_pct_PIB` e `population_faixa`. |

### Ouro
Mora em `dados/ouro/projeto.duckdb`, no schema `ouro`. O script `src/carga.py` cria os schemas `prata` e `ouro` e carrega os arquivos Parquet da Prata diretamente nas tabelas `prata.paises` e `prata.steam` via `read_parquet`. A partir daí, toda transformação da camada Ouro é escrita em SQL versionado, documentado e testado pelo **dbt** em `ecox14/models/`.

---

## As fontes

| Fonte | Origem | Uma linha é | Formato na Bronze | Acesso | Extraído em | Link |
|---|---|---|---|---|---|---|
| Steam Games Dataset (Daily Updates) | Kaggle (`hubertsidorowicz/steam-games-dataset-daily-updates`) | um jogo listado na loja Steam | CSV intacto (`955,97 MB`) | `kagglehub`, público | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates) |
| World Bank World Development Indicators | Kaggle (`nicolasgonzalezmunoz/world-bank-world-development-indicators`) | uma entidade (país ou agregado) em um ano (`1960–2023`) | CSV intacto (`5,19 MB`) | `kagglehub`, público | 14/10/2026 | [Kaggle](https://www.kaggle.com/datasets/nicolasgonzalezmunoz/world-bank-world-development-indicators) |

### Chaves primárias das fontes
- **Steam Store (`steam.parquet`):** `app_id` (identificador único do jogo na Steam).
- **Banco Mundial (`paises.parquet`):** chave composta `(country_chave, date)` — uma linha por país e ano na série histórica da Prata (`1960–2022`).

### Defeitos encontrados nas fontes
- **Steam Store:** registros de preço com valores ausentes ou texto inválido; registros sem título (`name` nulo ou vazio); valores extremos (*outliers*) muito altos que distorcem médias; presença de jogos gratuitos (`price = 0`), que não representam barreira financeira de compra.
- **Banco Mundial (WDI):** mistura de agregados regionais, demográficos e grupos de renda (ex.: `World`, `Euro area`, `High income`, `OECD members`) junto aos países individuais; coluna `date` em formato ISO completo (`1960-01-01`) em vez de ano inteiro; espaços extras e variações históricas de nomes de países (`United States`/`USA`, `Czech Republic`/`Czechia`, `Turkey`/`Turkiye`, `Viet Nam`/`Vietnam`); ausência de PIB (`GDP_current_US`) ou população (`population`) em diversos pares país-ano.

---

## Decisões de tratamento

### Steam Store (`src/transformar_steam.py`)
- **Entrada Bronze:** `143.333` registros (`steam_games_20261014.csv`).
- **Filtro de colunas:** mantidas `app_id`, `name` e `price`.
- **Limpeza de espaços:** removidos espaços nas extremidades de nomes de colunas e strings via `src/limpeza.py`.
- **Unicidade (`app_id`):** `0` duplicatas encontradas.
- **Preços vazios ou inválidos:** `price` convertido com `pd.to_numeric(..., errors="coerce")`; removidos **`1.321`** jogos sem preço válido.
- **Nomes ausentes ou vazios (`tratar_nomes`):** removidos **`2`** jogos sem título válido (`1` gratuito e `1` pago). Motivo: erro de cadastro que impede exibição legível no catálogo e no painel.
- **Valores extremos (*outliers*):** marcados **`6.750`** jogos em `price_extremo` pelo método IQR (`Q1 - 1,5*IQR` a `Q3 + 1,5*IQR`, intervalo `[-12,51; 23,49]`), mantendo todas as linhas na tabela por serem extremos legítimos de mercado.
- **Saída Prata (`dados/prata/steam.parquet`):** **`142.010`** registros (`113.921` jogos pagos + `28.089` gratuitos).

### Banco Mundial (`src/transformar_paises.py`)
- **Entrada Bronze:** `17.272` registros (`world_bank_development_indicators_20261014.csv`, `274` entidades de 1960 a 2023).
- **Filtro de colunas:** mantidas `country`, `date`, `GDP_current_US`, `population` e `inflation_annual%`.
- **Limpeza e tipagem:** espaços removidos; `date` convertida de texto ISO (`AAAA-MM-DD`) para ano inteiro (`Int64`); indicadores convertidos para numérico.
- **Preservação do rótulo e criação de chave (`padronizar_pais`):** `country` mantém o nome legível original (ex.: `Brazil`, `United States`) para exibição, enquanto `country_chave` recebe `chave_texto()` + `MAPA_PAISES` para comparação e junção.
- **Remoção de agregados regionais e grupos de renda (`remover_agregados`):** removidas **`3.291`** linhas correspondentes a **`54`** entidades agregadas. Motivo: granularidade diferente da dos países individuais.
- **Falta de dados essenciais (`tratar_vazios`):** removidas **`3.512`** linhas sem país, ano, PIB ou população (etapa aplicada antes da checagem de unicidade para evitar manter linhas vazias em caso de sinônimos).
- **Unicidade (`country_chave`, `date`):** `0` duplicatas encontradas após a limpeza.
- **Saída Prata (`dados/prata/paises.parquet`):** **`10.469`** registros cobrindo **`214`** países distintos entre **1960 e 2022**.

---

## Atributos derivados

### Camada Prata
- **`variacao_pct_PIB` (`paises.parquet`):** variação percentual anual do PIB (`GDP_current_US`) por país em relação ao ano imediatamente anterior. Ordena por `(country_chave, date)`, aplica `pct_change(fill_method=None) * 100` e exige anos consecutivos (`diff(date) == 1`). Fica ausente no primeiro ano de cada país ou após lacunas (`10.238` preenchidos e `231` ausentes).
- **`population_faixa` (`paises.parquet`):** classificação populacional em quartis **calculados por ano** (`groupby("date")`) com os rótulos `muito pequeno`, `pequeno`, `grande` e `muito grande`, evitando misturar portes populacionais de décadas distintas.

### Camada Ouro (`ecox14/models/fato_acessibilidade.sql`)
- **`pib_per_capita`:** PIB per capita anual em dólares correntes (`pib / populacao`).
- **`indice_acessibilidade`:** métrica que só existe após o cruzamento das duas fontes, medindo o peso relativo do preço do jogo em USD sobre o PIB per capita do país, escalado por `100.000`:
  $$\text{indice\_acessibilidade} = \left(\frac{\text{preco\_usd}}{\text{pib\_per\_capita}}\right) \times 100.000$$
  Quanto **maior** o índice, **menos acessível** é o jogo naquele país.

---

## Junção e cruzamento

Como a base do Banco Mundial (WDI) já consolida país, ano, PIB, população e inflação em uma única tabela e a base da Steam não possui coluna de país, o cruzamento entre jogos e países é um produto cartesiano (`CROSS JOIN`) de **24,3 milhões de linhas**. Seguindo a diretriz de **deixar o banco executar junções que não cabem confortavelmente na memória em pandas**, o cruzamento não é materializado em Parquet na Prata, sendo realizado diretamente no **DuckDB via dbt** na Camada Ouro.

### Quem ficou de fora no cruzamento (perdas documentadas)
- **Anos históricos anteriores em `paises.parquet` (`10.255` linhas):** a série completa `1960–2022` (`10.469` linhas) continua preservada em `dados/prata/paises.parquet` e `prata.paises`, mas `ouro.dim_pais` seleciona o **último ano com PIB e população válidos (`> 0`) por país** (**`214`** linhas, com ano de referência entre `2011` e `2022`). Isso evita cruzar preços atuais da Steam (2026) contra PIBs de décadas passadas (como 1960) e impede uma explosão cartesiana para ~1,5 bilhão de linhas.
- **Jogos gratuitos na Steam (`28.089` linhas):** permanecem na dimensão `ouro.dim_steam` (`142.010` jogos) para manter o catálogo íntegro, mas são filtrados de `ouro.fato_acessibilidade` (`preco_usd > 0`, restando **`113.921`** jogos pagos), pois preço zero não representa barreira financeira em USD.

---

## O modelo da camada Ouro

Um esquema estrela com uma tabela fato, duas dimensões e uma view de consumo no schema `ouro` de `dados/ouro/projeto.duckdb`.

| Modelo | Tipo | Grão | Colunas | Linhas |
|---|---|---|---|---:|
| `ouro.dim_pais` | dimensão (`table`) | um país | `pais_id`, `nome_pais`, `ano_referencia`, `pib`, `populacao`, `inflacao_anual`, `faixa_populacional`, `variacao_pib` | `214` |
| `ouro.dim_steam` | dimensão (`table`) | um jogo | `jogo_id`, `nome_jogo`, `preco_usd`, `flag_preco_extremo` | `142.010` |
| `ouro.fato_acessibilidade` | fato (`table`) | um jogo pago em um país no seu ano mais recente | `pais_id`, `ano`, `jogo_id`, `preco_usd`, `pib`, `populacao`, `pib_per_capita`, `indice_acessibilidade` | `24.379.094` |
| `ouro.vw_acessibilidade_completa` | view de consulta (`view`) | um jogo pago em um país no seu ano mais recente | colunas da fato + `nome_pais`, `faixa_populacional`, `nome_jogo`, `flag_preco_extremo` | `24.379.094` |

```text
dim_pais (1) ──────< (N) fato_acessibilidade (N) >────── (1) dim_steam
  pais_id                 pais_id, ano, jogo_id                jogo_id
```

### Declaração explícita do grão
> **Uma linha de `ouro.fato_acessibilidade` representa um jogo pago da Steam avaliado em um país no seu ano econômico mais recente: grão `(pais_id, ano, jogo_id)` (`214 × 113.921 = 24.379.094` linhas).**

---

## Testes e documentação

Todos os **24 testes automatizados** moram no dbt e são executados automaticamente na etapa `testes` do `src/pipeline.py` (ou isoladamente rodando `dbt test` dentro de `ecox14/`).

| Teste | Onde | O que garante |
|---|---|---|
| `unique` e `not_null` em `dim_pais.pais_id` | `ecox14/models/schema.yml` | Cada país aparece exatamente uma vez na dimensão e tem chave válida |
| `unique` e `not_null` em `dim_steam.jogo_id` | `ecox14/models/schema.yml` | Cada jogo aparece exatamente uma vez no catálogo e tem chave válida |
| `not_null` em `dim_pais.nome_pais` e `dim_steam.nome_jogo` | `ecox14/models/schema.yml` | Nenhum país ou jogo chega sem rótulo legível ao painel |
| `accepted_values` em `dim_pais.faixa_populacional` | `ecox14/models/schema.yml` | Apenas os 4 quartis válidos (`muito pequeno`, `pequeno`, `grande`, `muito grande`) |
| `not_null` nas chaves e métricas de `fato_acessibilidade` | `ecox14/models/schema.yml` | Nenhuma linha da fato fica sem `pais_id`, `ano`, `jogo_id`, `preco_usd`, `pib`, `populacao`, `pib_per_capita` ou `indice_acessibilidade` |
| `relationships` de `fato_acessibilidade.pais_id` → `dim_pais.pais_id` | `ecox14/models/schema.yml` | Nenhum fato órfão sem país correspondente na dimensão |
| `relationships` de `fato_acessibilidade.jogo_id` → `dim_steam.jogo_id` | `ecox14/models/schema.yml` | Nenhum fato órfão sem jogo correspondente na dimensão |
| `grao_fato_acessibilidade` | `ecox14/tests/grao_fato_acessibilidade.sql` | Teste singular: devolve `0` linhas, provando ausência de duplicatas em `(pais_id, ano, jogo_id)` |

Na última validação completa do pipeline, todos os **24 testes passaram (`PASS=24 WARN=0 ERROR=0`)** e o catálogo navegável foi gerado sem avisos via `dbt docs generate` (executado em `ecox14/`). Não há testes unitários automatizados para o código Python das camadas Bronze e Prata.

---

## O painel

```powershell
streamlit run dashboard/painel.py
```

Execute a partir da raiz do projeto, com o `.venv` ativado e o banco `dados/ouro/projeto.duckdb` já construído pelo pipeline.

O que o painel oferece:
- **Filtros na barra lateral (`st.sidebar`):**
  - Faixa populacional (`Todas` ou um dos 4 quartis populacionais).
  - Faixa de preço em USD (todos os jogos pagos ou recortes de preço).
  - Critério de ordenação (*Menos acessíveis* — maior índice vs. *Mais acessíveis* — menor índice).
  - Busca e seleção de um jogo específico (ex.: *Counter-Strike*) para comparar o peso real do preço em USD entre países.
- **Visualizações principais:**
  - Gráfico de barras (`st.bar_chart`) com o ranking dos países pelo Índice de Acessibilidade.
  - Tabelas detalhadas (`st.dataframe`, sem índice) exibindo `nome_pais`, ano de referência, faixa populacional, PIB per capita, preço em USD e índice calculado.
  - Rodapé (`st.caption`) informando as fontes (Steam Store e Banco Mundial — Kaggle), a data de extração (`14/10/2026`) e a contagem de registros exibidos.

Todo o SQL fica isolado em `dashboard/consultas.py`, em consultas estáticas com parâmetros `?` (zero concatenação de strings e zero f-strings em SQL), abrindo o DuckDB exclusivamente em modo `read_only=True` com fechamento garantido. `dashboard/painel.py` contém zero linhas de SQL e cuida apenas da interface.

---

## Decisões de projeto

- **DuckDB local, sem servidor:** todo o banco analítico cabe em um único arquivo (`dados/ouro/projeto.duckdb`), sem serviço para subir ou credenciais para configurar. Ele lê Parquet diretamente (`read_parquet` em `carga.py`) e integra-se nativamente ao dbt.
- **`ecox14/profiles.yml` versionado no repositório:** como o DuckDB é um banco local em arquivo (sem usuário, senha ou token), o perfil do dbt não contém nenhum segredo e usa caminho relativo (`../dados/ouro/projeto.duckdb`). Versioná-lo dentro de `ecox14/` elimina configuração manual em `~/.dbt/profiles.yml` e permite rodar o projeto imediatamente após `git clone`.
- **CSV na Bronze, Parquet na Prata:** a Bronze preserva os dados como vieram da origem; a Prata salva em Parquet tipado para que datas (`Int64`), preços (`float64`) e flags (`bool`) cheguem ao DuckDB sem reconversões.
- **Bronze imutável com data no nome:** novas extrações nunca sobrescrevem arquivos anteriores. Junto dos arquivos `proveniencia.jsonl`, isso garante rastreabilidade completa de cada número.
- **Tabela fato materializada como `table` e consumo como `view`:** como `fato_acessibilidade` cruza 24,3 milhões de linhas, materializar `dim_pais`, `dim_steam` e `fato_acessibilidade` como tabelas no DuckDB faz as agregações do painel responderem em menos de 1 segundo, enquanto `vw_acessibilidade_completa` permanece como view para evitar duplicar armazenamento e manter os rótulos sempre sincronizados.
- **Rótulo legível separado da chave de comparação:** `chave_texto()` gera `country_chave` (minúsculas sem acentos) para normalização e junções, mas `country` preserva o nome legível (`Brazil`, `United States`) para exibição no painel.
- **Outliers marcados, erros comprovados removidos:** jogos muito caros podem ser legítimos na Steam, portanto são apenas sinalizados via IQR (`price_extremo`). Já registros sem preço ou sem título, assim como agregados regionais misturados com países, são erros de domínio ou granularidade — por isso são removidos e contabilizados no `proveniencia.jsonl`.
- **SQL fora da tela do Streamlit:** SQL de transformação vive versionado e testado no dbt; SQL de leitura fica encapsulado em funções parametrizadas em `dashboard/consultas.py`, mantendo `dashboard/painel.py` limpo e focado na experiência visual.

---

## Governança e LGPD

- **Ausência de dados pessoais:** o projeto utiliza exclusivamente bases públicas e agregadas (catálogo público de jogos e indicadores macroeconômicos nacionais). Nenhum dado pessoal identificável é coletado, armazenado ou processado.
- **Rastreabilidade (FAIR):** todas as extrações da Bronze e transformações da Prata ficam registradas de forma acumulativa nos arquivos `proveniencia.jsonl` (versionados no Git), e o painel exibe no rodapé a origem, a data de extração e o volume de registros apresentados.