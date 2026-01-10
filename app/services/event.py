from datetime import datetime, timedelta
import asyncio
import logging
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.event import EventSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self.id_user_based = RecurrenceMode.USER_BASED.value
        self.id_expired_date = RecurrenceMode.EXPIRED_DATE.value
        self.id_calendar = RecurrenceMode.CALENDAR.value
    
    async def _expire_event_missions(
        self,
        db: AsyncSession,
        event_id: int,
        status_ids: list[int],
        id_expired: int
    ) -> None:
        """Expira as missões de um evento para os status fornecidos."""
        try:
            mission_types = await MissionTypeSchemaBase.get_all_mission_types_by_event_id(db, event_id)
            
            for mission_type_id in mission_types:
                await MissionSchemaBase.update_missions_status_by_type_and_status(
                    db, mission_type_id, status_ids, id_expired
                )
            
            logger.info(f"Event {event_id}: {len(mission_types)} mission types invalidated with statuses {status_ids}")
        except Exception as e:
            logger.error(f"Error expiring missions for event {event_id}: {e}")
            raise
        
    # Function that will "activate" and "deactivate" events
    async def update_status_events(self):
        async with Session() as session:
            db: AsyncSession = session

            now = datetime.now()
            # print(f"Current time: {now}")
            # Get status IDs in parallel
            status_names = ["active", "pending_confirmation", "completed", "expired"]
            id_active, id_pending, id_completed, id_expired = await asyncio.gather(
                *(StatusSchemaBase.get_id_by_name(db, name) for name in status_names)
            )
            
            # Get all pending events
            all_pending_events = await EventSchemaBase.get_all_active_events_by_user_type_and_status(
                db, list(range(0, 10)), [id_pending]  # List all user types, pending status
            )
            
            # For all pending events, check if it's time to activate them
            for event in all_pending_events:
                # print(f"Checking event {event.id} for activation...")
                start_date = event.start_date
                reset_time = event.reset_time
                
                if start_date is not None and reset_time:
                    start_date = (
                        start_date.replace(
                            hour=reset_time.hour,
                            minute=reset_time.minute,
                            second=reset_time.second,
                            microsecond=reset_time.microsecond
                        )
                    )
                elif start_date is not None:
                    start_date = start_date + timedelta(days=1)
                else:
                    start_date = None
                
                # Check if current date is >= start_date, if so, change event status to active
                if start_date and now >= start_date:
                    # print(f"Event {event.id} is ready to be activated.")
                    await EventSchemaBase.update_event_status(db, event.id, id_active)
                

            # Now get all active events and check if they are in the expiration period
            all_active_events = await EventSchemaBase.get_all_active_events_by_user_type_and_status(
                db, list(range(0, 10)), [id_active]  # List all user types, active status
            )
            
            for event in all_active_events:
                reset_time = event.reset_time
                auto_renew = event.auto_renew
                expiration_date = event.expired_date
                # print(f"Checking event {event.id} for expiration...")
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
                            if auto_renew:
                                # Event will be renewed automatically - expire ALL missions from the previous event
                                logger.info(f"Event {event.id} expired (auto_renew=True). Expiring all previous missions.")
                                await self._expire_event_missions(
                                    db, event.id, [id_active, id_pending, id_completed], id_expired
                                )
                            else:
                                # If not auto_renew, change the event status to expired
                                logger.info(f"Event {event.id} expired (auto_renew=False). Marking as expired.")
                                await EventSchemaBase.update_event_status(db, event.id, id_expired)
                                
                                # Invalidate only completed missions related to this expired event
                                await self._expire_event_missions(db, event.id, [id_completed], id_expired)
                    except Exception as e:
                        logger.error(f"Error processing event {event.id} expiration: {e}")
                        await db.rollback()
