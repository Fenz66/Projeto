select
    p.pais_id,
    p.ano_referencia as ano,
    s.jogo_id,
    s.preco_usd,
    p.pib,
    p.populacao,
    (p.pib / p.populacao) as pib_per_capita,
    (s.preco_usd / (p.pib / p.populacao)) * 100000 as indice_acessibilidade
from {{ ref('dim_pais') }} p
cross join {{ ref('dim_steam') }} s
where p.pais_id is not null
  and p.ano_referencia is not null
  and p.populacao > 0
  and p.pib > 0
  and s.jogo_id is not null
  and s.preco_usd > 0
