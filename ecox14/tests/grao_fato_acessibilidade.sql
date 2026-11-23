-- Passa quando devolve ZERO linhas: comprova o grão (pais_id, ano, jogo_id)
select
    pais_id,
    ano,
    jogo_id,
    count(*) as total
from {{ ref('fato_acessibilidade') }}
group by pais_id, ano, jogo_id
having count(*) > 1
