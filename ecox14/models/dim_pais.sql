select
    country as pais_id,
    date as ano,
    "GDP_current_US" as pib,
    population as populacao,
    "inflation_annual%" as inflacao_anual,
    population_faixa as faixa_populacional,
    variacao_pct_PIB as variacao_pib
from {{ source('prata', 'paises') }}
where country is not null
  and date is not null
