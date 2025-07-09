from app.schemas.mission import MissionSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.status import StatusSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from datetime import datetime
from app.services.calendar import Calendar
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.services.websocket import ws_manager
from app.schemas.notification import NotificationSchema

class ConfirmMissionService:
    
    def __init__(self):
        self.id_user_based = RecurrenceMode.USER_BASED.value
        self.id_expired_date = RecurrenceMode.EXPIRED_DATE.value
        self.id_calendar = RecurrenceMode.CALENDAR.value
    
    
    async def confirm_mission(self, db, mission_type_id: int, user_id: int) -> bool:
        """
        Confirm a mission by its ID.

        Args:
            mission_id (st): The ID of the mission to confirm.
            user_id (str): The ID of the user confirming the mission.

        Returns:
            bool: True if the mission was confirmed successfully, False otherwise.
        """
        try:
            now = datetime.now()
            status_names = ["pending_confirmation", "completed", "expired"]
            id_pending, id_completed, id_expired = await asyncio.gather(
                *(StatusSchemaBase.get_id_by_name(db, name) for name in status_names)
            )

            print(f"Getting recurrence_mode for mission_type_id: {mission_type_id}")
            recurrence_mode = await MissionTypeSchemaBase.get_recurrence_mode_by_id(db, mission_type_id)
            print(f"recurrence_mode: {recurrence_mode}")

            print(f"Getting start_date for mission_type_id: {mission_type_id}")
            start_date = await MissionTypeSchemaBase.get_start_date_by_id(db, mission_type_id)
            print(f"start_date: {start_date}")

            print(f"Getting reset_time_str for mission_type_id: {mission_type_id}")
            reset_time_str = await MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id)
            print(f"reset_time_str: {reset_time_str}")

            print(f"Getting auto_renew for mission_type_id: {mission_type_id}")
            auto_renew = await MissionTypeSchemaBase.get_auto_renew_by_id(db, mission_type_id)
            print(f"auto_renew: {auto_renew}")

            print(f"Getting recurrence_type for mission_type_id: {mission_type_id}")
            recurrence_type = await MissionTypeSchemaBase.get_recurrence_type_by_id(db, mission_type_id)
            print(f"recurrence_type: {recurrence_type}")

            if recurrence_mode == self.id_calendar:
                print(f"Recurrence mode: {recurrence_mode}, Start date: {start_date}")
                start_date, end_date = Calendar().get_current_period(
                    recurrence_type=recurrence_type,
                    start_date=start_date,
                    reset_time_str=reset_time_str,
                    auto_renew=auto_renew
                )
                print(f"Recurrence mode: {recurrence_mode}, Start date: {start_date}, End date: {end_date}")
            elif recurrence_mode == self.id_expired_date:
                print(f"Recurrence mode: {recurrence_mode}, Start date: {start_date}, to aqui 1")
                end_date = await MissionTypeSchemaBase.get_expired_date_by_id(db, mission_type_id)
                if not end_date:
                    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                if end_date and reset_time_str:
                    end_date = end_date.replace(
                        hour=reset_time_str.hour,
                        minute=reset_time_str.minute,
                        second=reset_time_str.second,
                        microsecond=0
                    )
            elif recurrence_mode == self.id_user_based:
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

            mission_id = await MissionSchemaBase.get_id_by_user_and_types_and_period_and_status(
                session=db,
                user_id=user_id,
                mission_type_id=mission_type_id,
                start_date=start_date,
                end_date=end_date,
                status_ids=[id_pending, id_completed, id_expired]
            )
            mission_status = await MissionSchemaBase.get_status_by_mission_id(db, mission_id)

            if not mission_id or mission_status in [id_expired, id_completed]:
                return False

            if mission_status != id_pending:
                return False

            await MissionSchemaBase.update_mission_status(db, mission_id, id_completed)

            mission_type_name = await MissionTypeSchemaBase.get_name_by_id(db, mission_type_id)
            message = f" Missão {mission_type_name} concluida com sucesso!"
            notification = await NotificationSchema.create_notification(db, user_id, message)
            await ws_manager.send_notification(str(user_id), message, notification.id)

            return True
        except Exception as e:
            print(f"Erro ao confirmar missão: {e}")
            return False
