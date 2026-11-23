"""Painel interativo (somente leitura) para explorar a acessibilidade global na Steam."""

import streamlit as st

import consultas

st.set_page_config(page_title="Acessibilidade Global na Steam", layout="wide")

st.title("Acessibilidade Global de Jogos na Steam")
st.markdown(
    "Impacto da precificação padrão em **USD** frente ao **PIB per capita** dos países "
    "(quanto maior o índice, menos acessível é o jogo)."
)

# --- Filtros laterais (carregados diretamente das dimensões) ---
faixas_df = consultas.faixas_populacionais()
opcoes_faixa = ["Todas"] + faixas_df["faixa_populacional"].tolist()
faixa_sel = st.sidebar.selectbox("Faixa populacional", opcoes_faixa)

FAIXAS_PRECO = {
    "Todos os jogos pagos": (0.0, None),
    "Até US$ 10": (0.0, 10.0),
    "US$ 10 a US$ 30": (10.0, 30.0),
    "US$ 30 a US$ 60": (30.0, 60.0),
    "Acima de US$ 60": (60.0, None),
}
preco_label = st.sidebar.selectbox("Faixa de preço (USD)", list(FAIXAS_PRECO.keys()))
preco_min, preco_max = FAIXAS_PRECO[preco_label]

ORDENS = {
    "Menos acessíveis (maior índice)": "desc",
    "Mais acessíveis (menor índice)": "asc",
}
ordem_label = st.sidebar.selectbox("Ordenação", list(ORDENS.keys()))
ordem_sql = ORDENS[ordem_label]

st.sidebar.divider()
termo_jogo = st.sidebar.text_input("Buscar jogo específico (nome)", value="")
jogos_df = consultas.buscar_jogos(termo=termo_jogo, limite=50)

# --- Seção 1: Panorama por faixa de preço ---
dados_faixa = consultas.acessibilidade_por_faixa(
    faixa=faixa_sel,
    preco_min=preco_min,
    preco_max=preco_max,
    ordem=ordem_sql,
)

st.subheader(f"Top 10 países — {preco_label} ({ordem_label})")
col1, col2 = st.columns([3, 2])

with col1:
    st.bar_chart(
        dados_faixa.head(10),
        x="nome_pais",
        y="indice_acessibilidade",
    )

with col2:
    st.dataframe(dados_faixa, hide_index=True, width="stretch")

# --- Seção 2: Comparação de um jogo específico ---
st.divider()
st.subheader("Comparação por jogo específico")

if jogos_df.empty:
    st.info("Nenhum jogo pago encontrado para o termo informado.")
    qtd_jogo = 0
else:
    rotulos_jogos = [
        f"{row.nome_jogo} (US$ {row.preco_usd:.2f})" for row in jogos_df.itertuples()
    ]
    idx_jogo = st.sidebar.selectbox(
        "Selecionar jogo",
        options=range(len(rotulos_jogos)),
        format_func=lambda i: rotulos_jogos[i],
    )
    jogo_sel = jogos_df.iloc[idx_jogo]

    dados_jogo = consultas.acessibilidade_por_jogo(
        jogo_id=int(jogo_sel["jogo_id"]),
        faixa=faixa_sel,
        ordem=ordem_sql,
    )
    qtd_jogo = len(dados_jogo)

    st.markdown(
        f"**{jogo_sel['nome_jogo']}** — preço base: **US$ {jogo_sel['preco_usd']:.2f}**"
    )
    jcol1, jcol2 = st.columns([3, 2])

    with jcol1:
        st.bar_chart(
            dados_jogo.head(10),
            x="nome_pais",
            y="indice_acessibilidade",
        )

    with jcol2:
        st.dataframe(dados_jogo, hide_index=True, width="stretch")

st.caption(
    f"Fontes: Steam Store e Banco Mundial (Kaggle, extração em 14/10/2026). "
    f"Exibindo {len(dados_faixa)} países no panorama geral e {qtd_jogo} países na comparação por jogo."
)
