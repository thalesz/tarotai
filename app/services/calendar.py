from datetime import datetime, timedelta, time
import asyncio
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.recurrence_type import RecurrenceType
from app.schemas.user import UserSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase
from app.schemas.mission import MissionSchemaBase


class Calendar:
    def __init__(self):
        self.id_calendar = RecurrenceMode.CALENDAR.value

    def get_current_period(self, recurrence_type: int, start_date: datetime, reset_time_str: str, auto_renew: bool) -> tuple[datetime, datetime]:
        try:
            now = datetime.now()

            # Parse reset_time
            if isinstance(reset_time_str, str):
                reset_hour, reset_minute, reset_second = map(int, reset_time_str.split(":"))
                reset_time = time(hour=reset_hour, minute=reset_minute, second=reset_second)
            elif isinstance(reset_time_str, time):
                reset_time = reset_time_str
            else:
                raise ValueError("reset_time_str must be string or time")

            def apply_reset_time(date: datetime) -> datetime:
                return date.replace(hour=reset_time.hour, minute=reset_time.minute, second=reset_time.second, microsecond=0)

            start_date = apply_reset_time(start_date)

            if recurrence_type == RecurrenceType.DAILY.value:
                today_reset = apply_reset_time(now)
                if now < today_reset:
                    period_start = today_reset - timedelta(days=1)
                else:
                    period_start = today_reset
                period_end = period_start + timedelta(days=1)

            elif recurrence_type == RecurrenceType.WEEKLY.value:
                days_since_start = (now - start_date).days
                weeks_since_start = days_since_start // 7
                period_start = start_date + timedelta(weeks=weeks_since_start)
                period_end = period_start + timedelta(weeks=1)

            elif recurrence_type == RecurrenceType.MONTHLY.value:
                period_start = start_date
                while True:
                    next_month = (period_start.month % 12) + 1
                    year = period_start.year + (period_start.month // 12)
                    try:
                        period_end = period_start.replace(year=year, month=next_month)
                    except ValueError:
                        # ajuste para meses como fevereiro
                        period_end = (period_start + timedelta(days=31)).replace(day=1)
                    if period_start <= now < period_end:
                        break
                    period_start = period_end

            elif recurrence_type == RecurrenceType.YEARLY.value:
                year = start_date.year
                while True:
                    period_start = start_date.replace(year=year)
                    period_end = period_start.replace(year=year + 1)
                    if period_start <= now < period_end:
                        break
                    year += 1

            else:
                # fallback: 1 dia
                period_start = start_date
                period_end = period_start + timedelta(days=1)

            return period_start, period_end
        except Exception as e:
            print(f"Erro em get_current_period: {e}")
            raise

    async def calendar(self):
        async with Session() as session:
            db: AsyncSession = session

            id_active = await StatusSchemaBase.get_id_by_name(db, "active")
            id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")
            id_completed = await StatusSchemaBase.get_id_by_name(db, "completed")
            id_expired = await StatusSchemaBase.get_id_by_name(db, "expired")

            all_active_users = await UserSchemaBase.get_all_id_by_status(db, id_active)
            all_active_mission_types = await MissionTypeSchemaBase.get_all_id_by_status_and_recurrence_mode(db, id_active, self.id_calendar)

            for user_id in all_active_users:
                for mission_type_id in all_active_mission_types:
                    # Dados estáticos por missão
                    start_date, recurrence_type, reset_time_str, auto_renew = await asyncio.gather(
                        MissionTypeSchemaBase.get_start_date_by_id(db, mission_type_id),
                        MissionTypeSchemaBase.get_recurrence_type_by_id(db, mission_type_id),
                        MissionTypeSchemaBase.get_reset_time_by_id(db, mission_type_id),
                        MissionTypeSchemaBase.get_auto_renew_by_id(db, mission_type_id)
                    )
                    period_start, period_end = self.get_current_period(recurrence_type, start_date, reset_time_str, auto_renew)

                    id_missions = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                        session=db,
                        user_id=user_id,
                        mission_type_id=mission_type_id,
                        start_date=None,
                        end_date=period_start,
                        status_ids=[id_pending]
                    )

                    status_mission_type = await MissionTypeSchemaBase.get_status_by_id(db, mission_type_id)

                    for mission_id in id_missions:
                        created_at, status_instance = await asyncio.gather(
                            MissionSchemaBase.get_created_at_by_id(db, mission_id),
                            MissionSchemaBase.get_status_by_mission_id(db, mission_id)
                        )

                        # Lógica ajustada para expirar missões e instâncias pendentes
                        if created_at is None or not (period_start <= created_at < period_end) or status_mission_type == id_expired:
                            if status_mission_type == id_expired:
                                # Se a missão estiver expirada, todas as instâncias pendentes devem ser expiradas
                                if status_instance == id_pending:
                                    await MissionSchemaBase.update_mission_status(db, mission_id, id_expired)

                            elif auto_renew:
                                if status_instance == id_pending:
                                    await MissionSchemaBase.modified_created_at(db, mission_id, period_start)
                                elif status_instance == id_completed:
                                    exists_next = await MissionSchemaBase.get_id_by_user_and_types_and_period_and_status(
                                        session=db,
                                        user_id=user_id,
                                        mission_type_id=mission_type_id,
                                        start_date=period_end,
                                        end_date=None,
                                        status_ids=[id_pending, id_completed]
                                    )
                                    if not exists_next:
                                        await MissionSchemaBase.create_mission(db, mission_type_id, user_id)
                            else:
                                if status_instance == id_pending:
                                    await MissionSchemaBase.update_mission_status(db, mission_id, id_expired)

                    # Só verifica missões no período atual se o tipo de missão estiver ativo
                    if status_mission_type == id_active:
                        id_current = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                            session=db,
                            user_id=user_id,
                            mission_type_id=mission_type_id,
                            start_date=period_start,
                            end_date=period_end,
                            status_ids=[id_pending, id_completed]
                        )

                        if not id_current:
                            await MissionSchemaBase.create_mission(db, mission_type_id, user_id)

                        elif len(id_current) > 1:
                            # Otimiza as chamadas agrupando os resultados
                            status_map = {
                                mission_id: await MissionSchemaBase.get_status_by_mission_id(db, mission_id)
                                for mission_id in id_current
                            }

                            completed = [m for m, s in status_map.items() if s == id_completed]
                            pending = [m for m, s in status_map.items() if s == id_pending]

                            if completed:
                                for m in pending:
                                    await MissionSchemaBase.update_mission_status(db, m, id_expired)
                            elif len(pending) > 1:
                                for m in pending[1:]:
                                    await MissionSchemaBase.update_mission_status(db, m, id_expired)
