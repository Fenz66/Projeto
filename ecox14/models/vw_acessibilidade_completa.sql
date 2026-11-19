{{ config(materialized='view') }}

select
    f.pais_id,
    f.ano,
    f.jogo_id,
    d_pais.faixa_populacional,
    d_steam.nome_jogo,
    f.preco_usd,
    d_steam.flag_preco_extremo,
    f.pib_per_capita,
    f.indice_acessibilidade
from {{ ref('fato_acessibilidade') }} f
join {{ ref('dim_pais') }} d_pais
    on f.pais_id = d_pais.pais_id
   and f.ano = d_pais.ano
join {{ ref('dim_steam') }} d_steam
    on f.jogo_id = d_steam.jogo_id
