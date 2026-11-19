import logging
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
BRONZE = DADOS / "bronze"
BRONZE_STEAM = BRONZE / "steam"
BRONZE_BANCO_MUNDIAL = BRONZE / "banco_mundial"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"
RELATORIOS = RAIZ / "relatorios"
DBT_DIR = RAIZ / "ecox14"
BANCO_DUCKDB = OURO / "projeto.duckdb"

DATASET_STEAM = "hubertsidorowicz/steam-games-dataset-daily-updates"
DATASET_BANCO_MUNDIAL = "nicolasgonzalezmunoz/world-bank-world-development-indicators"

PADRAO_STEAM = "steam_games_*.csv"
PADRAO_BANCO_MUNDIAL = "world_bank_development_indicators_*.csv"

# Configuração centralizada dos logs (terminal + arquivo pipeline.log)
LOG_FILE = RAIZ / "pipeline.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
