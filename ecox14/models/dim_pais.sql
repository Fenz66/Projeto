select
    country_chave as pais_id,
    country as nome_pais,
    date as ano_referencia,
    "GDP_current_US" as pib,
    population as populacao,
    "inflation_annual%" as inflacao_anual,
    population_faixa as faixa_populacional,
    variacao_pct_PIB as variacao_pib
from {{ source('prata', 'paises') }}
where country_chave is not null
  and country is not null
  and date is not null
  and population > 0
  and "GDP_current_US" > 0
qualify row_number() over (partition by country_chave order by date desc) = 1
