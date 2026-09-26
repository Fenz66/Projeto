# Acessibilidade Global no Mercado de Jogos: O Impacto da Precificação Padrão (USD)

**Autor:** Caio Freitas Santos (Matrícula: 2025014153)

**Pergunta norteadora:** Como o preço base (em USD) dos jogos da Steam afeta a acessibilidade de compra em diferentes países, quando cruzado com os seus respetivos indicadores socioeconómicos (como PIB per capita e Paridade do Poder de Compra)?[cite: 7]

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Steam Games Dataset All Games 136K+ | CSV | KaggleHub | 27/08/2026 | [Kaggle](https://www.kaggle.com/datasets/hubertsidorowicz/steam-games-dataset-daily-updates) |
| World Bank World Development Indicators | CSV | KaggleHub | 27/08/2026 | [Kaggle](https://www.kaggle.com/datasets/nicolasgonzalezmunoz/world-bank-world-development-indicators) |

## Defeitos conhecidos das fontes

### Steam Store (Kaggle)
- Registo de preços com valores ausentes ou texto inválido.
- Presença de valores extremos (outliers) bastante altos que podem distorcer a média.
- Possibilidade de chaves duplicadas para o mesmo jogo (AppID).

### Banco Mundial
- Devolve agregados regionais misturados com os países.
- Nomes de países e regiões com espaços invisíveis no fim.
- Falta de dados essenciais (PIB e População) em determinados anos.
- O mesmo país escrito de formas diferentes (ex: USA e United States).

## Decisões de tratamento

### Steam Store
- Filtro de colunas: mantidas apenas as colunas relevantes ao Índice de Acessibilidade (app_id, name, price).
- Valores de preço vazios/inválidos: removidas 1270 ocorrências. Motivo: sem preço, o cruzamento perde utilidade.
- Valores extremos de preço: marcados 6690 outliers através do método IQR, mantendo a linha e sinalizando com uma nova coluna. Motivo: um jogo caro é um extremo legítimo e documentado, não um erro comprovado a ser eliminado.
- Chaves duplicadas: eliminadas 0 ocorrências pela chave primária AppID.

### Banco Mundial
- Espaços removidos de nomes de colunas e texto.
- Falta de dados financeiros (PIB e População): 148 linhas retiradas. Motivo: impossibilita a criação do índice financeiro.
- Padronização de nomes: países convertidos para letras minúsculas, sem acentos, e corrigidos através de um mapa de sinónimos para facilitar o cruzamento com a base da Steam.
- Duplicados de tempo e espaço: removidas 16998 linhas através da verificação da chave composta (país + ano).
- Coluna `date`: convertida para número inteiro.

## Atributos derivados

### variacao_pct_PIB
Variação percentual anual do PIB em relação ao ano anterior, calculada por país. Serve para comparar o ritmo de crescimento financeiro entre diferentes nações. Ausente no primeiro ano de cada país, por definição.

### population_faixa
Agrupamento em quartis de população (muito pequeno, pequeno, grande, muito grande). Serve para agrupar países com portes comparáveis sem ter de escolher um corte arbitrário de forma manual. 