import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
# Default is IB Gateway paper. Others: Gateway live 4001, TWS paper 7497, TWS live 7496.
IB_PORT = int(os.getenv("IB_PORT", "4002"))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", "1"))
DB_PATH = ROOT / os.getenv("DB_PATH", "data/portfolio.db")