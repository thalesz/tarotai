from datetime import datetime, timedelta
import asyncio
import logging
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.user import UserSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.event import EventSchemaBase

logger = logging.getLogger(__name__)

class MissionService:
    def __init__(self):
        self.id_user_based = RecurrenceMode.USER_BASED.value
        self.id_expired_date = RecurrenceMode.EXPIRED_DATE.value
        self.id_calendar = RecurrenceMode.CALENDAR.value

    async def _expire_missions_for_type(
        self,
        session: AsyncSession,
        mission_type_id: int,
        status_filter: list[int],
        status_to_set: int,
    ):
        """Marks all missions of a given type and status as expired."""
        await MissionSchemaBase.update_missions_status_by_type_and_status(
            session, mission_type_id, status_filter, status_to_set
        )
        
    #funcao que vai "ativar" e "desativar" as missoes
    async def update_status_missions(self):
        async with Session() as session:
            db: AsyncSession = session

            now = datetime.now()
            # print(f"Current time: {now}")
            # Obtenção de IDs de status em paralelo
            status_names = ["active", "pending_confirmation", "completed", "expired"]
            id_active, id_pending, id_completed, id_expired = await asyncio.gather(
                *(StatusSchemaBase.get_id_by_name(db, name) for name in status_names)
            )
            
            
            all_pending_mission_types = await MissionTypeSchemaBase.get_all_id_by_status_and_recurrence_mode(
                db, id_pending, [self.id_user_based, self.id_expired_date, self.id_calendar]
            )
            
            # para todas as missões pendentes, verificar se ta na data e hora de ligar, se tiver, ativa a missão mudando o status para ativo
            for mission_type_id in all_pending_mission_types:
                # print(f"Checking mission type {mission_type_id} for activation...")
                is_event_active = await EventSchemaBase.has_active_event_for_mission(
                    db, mission_type_id, id_active
                )

                if not is_event_active:
                    await self._expire_missions_for_type(
                        db, mission_type_id, [id_pending], id_expired
                    )
                    continue

                start_date = await MissionTypeSchemaBase.get_start_date_by_id(db, mission_type_id)
                reset_time = await MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id)
                
                if start_date is not None and reset_time:
                    start_date = (
                        (start_date).replace(
                            hour=reset_time.hour,
                            minute=reset_time.minute,
                            second=reset_time.second,
                            microsecond=reset_time.microsecond
                        )
                    )
                elif start_date is not None:
                    start_date = start_date + timedelta(days=start_date)
                else:
                    start_date = None
                
                # verifica se a data atual é maior ou igual a start_date, se for, muda o status da missão para ativo
                if start_date and now >= start_date:
                    # print(f"Mission type {mission_type_id} is ready to be activated.")
                    await MissionTypeSchemaBase.update_mission_type_status(db, mission_type_id, id_active)
                

            # agora vamos pegar todas as missões ativas e verificar se elas estão no período de expiração
            all_active_mission_types = await MissionTypeSchemaBase.get_all_id_by_status_and_recurrence_mode(
                db, id_active, [self.id_user_based, self.id_expired_date, self.id_calendar]
            )
            
            for mission_type_id in all_active_mission_types:
                is_event_active = await EventSchemaBase.has_active_event_for_mission(
                    db, mission_type_id, id_active
                )

                if not is_event_active:
                    await self._expire_missions_for_type(
                        db, mission_type_id, [id_pending], id_expired
                    )
                    continue

                reset_time = await MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id)
                auto_renew = await MissionTypeSchemaBase.get_auto_renew_by_id(db, mission_type_id)
                expiration_date = await MissionTypeSchemaBase.get_expired_date_by_id(db, mission_type_id)
                # print(f"Checking mission type {mission_type_id} for expiration...")
                # print(f"Reset time: {reset_time}, Expiration date: {expiration_date}")
                
                if expiration_date and reset_time:
                    expiration_date = expiration_date.replace(
                        hour=reset_time.hour,
                        minute=reset_time.minute,
                        second=reset_time.second,
                        microsecond=reset_time.microsecond
                    )
            
                # print(f"Current time: {now}, Expiration date: {expiration_date}")
                if expiration_date and now >= expiration_date:
                    try:
                        async with db.begin():
                            # tem que verificar se é auto_renew ou não
                            if auto_renew:
                                # não faz nada, pois a missão vai ser renovada automaticamente
                                logger.info(f"Mission {mission_type_id} expired (auto_renew=True). Will be renewed automatically.")
                            else:
                                # se não for auto_renew, muda o status da missão para expirado
                                logger.info(f"Mission {mission_type_id} expired (auto_renew=False). Marking as expired.")
                                await MissionTypeSchemaBase.update_mission_type_status(db, mission_type_id, id_expired)
                    except Exception as e:
                        logger.error(f"Error processing mission {mission_type_id} expiration: {e}")
                        await db.rollback()
                    
            

          