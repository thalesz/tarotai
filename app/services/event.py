from datetime import datetime, timedelta
import asyncio
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchemaBase
from app.schemas.recurrence_mode import RecurrenceMode
from app.schemas.event import EventSchemaBase

class EventService:
    def __init__(self):
        self.id_user_based = RecurrenceMode.USER_BASED.value
        self.id_expired_date = RecurrenceMode.EXPIRED_DATE.value
        self.id_calendar = RecurrenceMode.CALENDAR.value
        
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
                    # Must check if it's auto_renew or not
                    if auto_renew:
                        # Does nothing, as the event will be renewed automatically
                        print(f"Event {event.id} is expired, but will be renewed automatically.")
                        # await EventSchemaBase.update_event_status(db, event.id, id_pending)
                    else:
                        # If not auto_renew, change the event status to expired
                        print(f"Event {event.id} is expired and will not be renewed automatically.")
                        await EventSchemaBase.update_event_status(db, event.id, id_expired)
