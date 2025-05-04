from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.postgresdatabase import engine, Session
from app.core.base import Base

# Isso garante que todos os modelos sejam registrados no metadata
from app.models import __all_models
from app.models.user import UserModel
from app.models.wallet import WalletModel
from app.models.deck import DeckModel
from app.models.status import StatusModel
from app.models.card import CardModel
from app.models.user_type import UserTypeModel
from app.models.spread_types import SpreadTypeModel
from app.models.draw import DrawModel

from app.schemas.user_type import UserTypeSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.card import CardSchemaBase
from app.schemas.deck import DeckSchemaBase
from app.schemas.spread_type import SpreadTypeSchema
from app.schemas.topic import TopicSchemaBase

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        print("📌 Modelos registrados:")
        for table_name in Base.metadata.tables.keys():
            print(f"➡ {table_name}")

        print("💾 Criando tabelas no banco (se ainda não existirem)...")
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        db: AsyncSession = session
        await UserTypeSchemaBase.sync_user_types(db)
        await StatusSchemaBase.sync_statuses(db)
        await DeckSchemaBase.sync_decks(db)
        await CardSchemaBase.sync_cards(db)
        await SpreadTypeSchema.sync_spread_types(db)
        await TopicSchemaBase.sync_topics(db)
        print("💾 Tabelas adicionadas!")
    yield
