from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

base_dir = Path(__file__).resolve().parent

# Prefer an explicit DATABASE_URL; fallback to the provided Aiven connection string.
DATABASE_URL = os.getenv("DATABASE_URL")

# Use CA certificate for TLS if available (required by Aiven).
CA_CERT_PATH = os.getenv("DB_SSL_CA_PATH", str(base_dir / "aiven_ca.pem"))

connect_args = {}
if CA_CERT_PATH and Path(CA_CERT_PATH).exists():
    connect_args = {
        "ssl_ca": CA_CERT_PATH,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()