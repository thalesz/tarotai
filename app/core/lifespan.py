from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.postgresdatabase import engine
from app.core.base import Base  # Certifique-se de que este Base vem do declarative_base correto

# Isso garante que todos os modelos sejam registrados no metadata
from app.models import __all_models
from app.models.user import UserModel  # Adicione explicitamente qualquer modelo adicional aqui
from app.models.wallet import WalletModel  # Adicione explicitamente qualquer modelo adicional aqui
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        print("📌 Modelos registrados:")
        for table_name in Base.metadata.tables.keys():
            print(f"➡ {table_name}")
        
        print("💾 Criando tabelas no banco (se ainda não existirem)...")
        await conn.run_sync(Base.metadata.create_all)
    
    yield
