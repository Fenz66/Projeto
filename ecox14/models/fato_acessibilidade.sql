with ultimo_ano_pais as (
    select
        pais_id,
        ano,
        pib,
        populacao
    from {{ ref('dim_pais') }}
    where pais_id is not null
      and ano is not null
      and populacao > 0
      and pib > 0
    qualify row_number() over (partition by pais_id order by ano desc) = 1
),
jogos_pagos as (
    select
        jogo_id,
        preco_usd
    from {{ ref('dim_steam') }}
    where jogo_id is not null
      and preco_usd > 0
)

select
    p.pais_id,
    p.ano,
    s.jogo_id,
    s.preco_usd,
    p.pib,
    p.populacao,
    (p.pib / p.populacao) as pib_per_capita,
    (s.preco_usd / (p.pib / p.populacao)) * 100000 as indice_acessibilidade
from ultimo_ano_pais p
cross join jogos_pagos s
