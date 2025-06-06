from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.postgresdatabase import engine, Session
from app.core.base import Base
import asyncio
import datetime

from app.models import __all_models
from app.schemas.user_type import UserTypeSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.card import CardSchemaBase
from app.schemas.deck import DeckSchemaBase
from app.schemas.spread_type import SpreadTypeSchema
from app.schemas.topic import TopicSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.user import UserSchemaBase
from app.schemas.event import EventSchemaBase
from app.schemas.reading_style import ReadingStyleSchemaBase


from app.services.dailyScheduler import DailyScheduler
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.recurrence_type import RecurrenceType
from app.services.subscription import Subscription
from app.services.calendar import Calendar

from contextlib import asynccontextmanager
from app.services.scheduler import start_jobs

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Criação das tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Inicialização dos dados
    async with Session() as session:
        db: AsyncSession = session
        await UserTypeSchemaBase.sync_user_types(db)
        await StatusSchemaBase.sync_statuses(db)
        await DeckSchemaBase.sync_decks(db)
        await CardSchemaBase.sync_cards(db)
        await SpreadTypeSchema.sync_spread_types(db)
        await TopicSchemaBase.sync_topics(db)
        await MissionTypeSchemaBase.sync_mission_types(db)
        await EventSchemaBase.sync_events(db)
        await ReadingStyleSchemaBase.sync_reading_styles(db)

    # Inicia o agendador
    start_jobs()
    provide_daily_gifts = DailyScheduler(
        scheduled_time=datetime.time(hour=18, minute=30),
        functions=[Subscription().create_daily_gift_for_all_users]
    )

    asyncio.create_task(provide_daily_gifts.start())

    yield