from datetime import datetime, timedelta
import asyncio
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.user import UserSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from app.schemas.mission import MissionSchemaBase

class UserBased:
    def __init__(self):
        self.id_user_based = RecurrenceMode.USER_BASED.value

    @staticmethod
    def calculate_expired_date(start_date: datetime, relative_days: int, reset_time) -> datetime:
        if relative_days is not None and reset_time:
            expired_date = (
                (start_date + timedelta(days=relative_days)).replace(
                    hour=reset_time.hour,
                    minute=reset_time.minute,
                    second=reset_time.second,
                    microsecond=reset_time.microsecond
                )
            )
        elif relative_days is not None:
            expired_date = start_date + timedelta(days=relative_days)
        else:
            expired_date = None
        return expired_date
    
    
    async def user_based(self):
        async with Session() as session:
            db: AsyncSession = session

            now = datetime.now()

            # Obtenção de IDs de status em paralelo
            status_names = ["active", "pending_confirmation", "completed", "expired"]
            id_active, id_pending, id_completed, id_expired = await asyncio.gather(
                *(StatusSchemaBase.get_id_by_name(db, name) for name in status_names)
            )

            all_active_users = await UserSchemaBase.get_all_id_by_status(db, id_active)

            # print(f"All active users: {all_active_users}")

            all_active_mission_types = await MissionTypeSchemaBase.get_all_id_by_status_and_recurrence_mode(
                db, [id_active, id_expired], self.id_user_based
            )

            for mission_type_id in all_active_mission_types:
                # Buscar todos os dados de uma vez (pode ser otimizado no banco também)
                relative_days, reset_time = await asyncio.gather(
                    # MissionTypeSchemaBase.get_start_date_by_id(db, mission_type_id),
                    MissionTypeSchemaBase.get_relative_days_by_id(db, mission_type_id),
                    MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id)
                )

                # if not start_date:
                #     continue

                statusMission = await MissionTypeSchemaBase.get_status_by_id(db, mission_type_id)


                for user_id in all_active_users:
                    mission_ids = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                        session=db,
                        user_id=user_id,
                        mission_type_id=mission_type_id,
                        start_date=None,
                        end_date=None,
                        status_ids=[id_pending, id_completed]
                    )
                    
                    
                    for mission_id in mission_ids:
                        # Verificar se a missão já existe
                        if not mission_id:
                            continue
                        
                        # Obter dados da missão
                        start_date = await MissionSchemaBase.get_created_at_by_id(db, mission_id) if mission_id else None
                    
                        expired_date = self.calculate_expired_date(start_date, relative_days, reset_time)
                        

                        if (expired_date and now >= expired_date and mission_id) or (statusMission == id_expired):
                            
                            statusMissionInstance = await MissionSchemaBase.get_status_by_mission_id(session=db, mission_id=mission_id)
                            if statusMissionInstance == id_pending:
                                await MissionSchemaBase.update_mission_status(db, mission_id, id_expired)
                                # print(f"Missão {mission_type_id} do usuário {user_id} expirou e não será auto-renovada.")
                            else:
                                print(f"Missão {mission_type_id} do usuário {user_id} já está concluída ou expirada.")
