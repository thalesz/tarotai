from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.calendar import Calendar
from app.services.expired import Expired
from app.services.user_based import UserBased
from app.services.mission import MissionService

scheduler = AsyncIOScheduler()

def start_jobs():
    calendar = Calendar()
    expired = Expired()
    user_based = UserBased()
    mission = MissionService()

    async def executar_em_ordem():
        await mission.update_status_missions()
        await calendar.calendar()
        await expired.expired()
        await user_based.user_based()

    scheduler.add_job(
        executar_em_ordem,
        trigger=IntervalTrigger(minutes=1),
        id="sequencial_task",
        name="Execução sequencial de todas as tarefas",
        replace_existing=True,
    )

    scheduler.start()
