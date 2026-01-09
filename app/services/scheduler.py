from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.calendar import Calendar
from app.services.expired import Expired
from app.services.user_based import UserBased
from app.services.mission import MissionService
from app.services.event import EventService
from app.services.subscription import Subscription
from app.core.postgresdatabase import Session


scheduler = AsyncIOScheduler()

def start_jobs():
    subscription = Subscription()
    # subscription.async_init()  # Initialize subscription service
    calendar = Calendar()
    expired = Expired()
    user_based = UserBased()
    mission = MissionService()
    event = EventService()
    

    async def executar_em_ordem():
        await subscription.verify_subscription()
        await mission.update_status_missions()
        await event.update_status_events()
        await calendar.calendar()
        await expired.expired()
        await user_based.user_based()
        
        # criar um serviço que adiciona as tiragens diarias de acordo com o tipo de usuario 
        
        

    scheduler.add_job(
        executar_em_ordem,
        trigger=IntervalTrigger(minutes=1),
        id="sequencial_task",
        name="Execução sequencial de todas as tarefas",
        replace_existing=True,
    )

    scheduler.start()
