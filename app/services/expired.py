from datetime import datetime
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.user import UserSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from app.schemas.mission import MissionSchemaBase

class Expired:
    def __init__(self):
        self.id_expired_date = RecurrenceMode.EXPIRED_DATE.value

    async def expired(self):
        async with Session() as session:
            db: AsyncSession = session

            # Buscar IDs dos status
            id_active = await StatusSchemaBase.get_id_by_name(db, "active")
            id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")
            id_completed = await StatusSchemaBase.get_id_by_name(db, "completed")
            id_expired = await StatusSchemaBase.get_id_by_name(db, "expired")

            # Buscar todos os usuários ativos
            all_active_users = await UserSchemaBase.get_all_id_by_status(db, id_active)
            # print(f"Usuários ativos encontrados: {all_active_users}")

            # Buscar todos os tipos de missão ativos com modo EXPIRED_DATE
            all_active_mission_types = await MissionTypeSchemaBase.get_all_id_by_status_and_recurrence_mode(
                db, [id_active, id_expired], self.id_expired_date
            )

            for mission_type_id in all_active_mission_types:
                start_date = await MissionTypeSchemaBase.get_start_date_by_id(db, mission_type_id)
                expired_date = await MissionTypeSchemaBase.get_expired_date_by_id(db, mission_type_id)
                reset_time = await MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id)
                mission_type_status = await MissionTypeSchemaBase.get_status_by_id(db, mission_type_id)
                # Ajustar hora da data de expiração
                if expired_date and reset_time:
                    expired_date = expired_date.replace(
                        hour=reset_time.hour,
                        minute=reset_time.minute,
                        second=reset_time.second,
                        microsecond=reset_time.microsecond
                    )

                for user_id in all_active_users:
                    # Buscar missões existentes do tipo dentro do período
                    existing_missions_ids = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                        session=db,
                        user_id=user_id,
                        mission_type_id=mission_type_id,
                        start_date=None,
                        end_date=None,
                        status_ids=[id_pending, id_completed]
                    )
                    
                    for mission_id in existing_missions_ids:
                        # Verificar e atualizar status se necessário
                        status_current = await MissionSchemaBase.get_status_by_mission_id(db, mission_id)

                        if (datetime.now() >= expired_date and status_current == id_pending) or mission_type_status == id_expired:
                            await MissionSchemaBase.update_mission_status(db, mission_id, id_expired)
                            # print(f"Missão {mission_id} do usuário {user_id} marcada como expirada.")

                    # Criar missão se não existir e estiver dentro do intervalo
                    if not existing_missions_ids and start_date and expired_date and start_date <= datetime.now() < expired_date and id_expired != mission_type_status:
                        await MissionSchemaBase.create_mission(db, mission_type_id, user_id)
                        # print(f"Missão criada para usuário {user_id}, tipo {mission_type_id}")
                    # Fim do código 


