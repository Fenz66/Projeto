select
    app_id as jogo_id,
    name as nome_jogo,
    price as preco_usd,
    price_extremo as flag_preco_extremo
from {{ source('prata', 'steam') }}
where app_id is not null
