from pydantic import BaseModel
from sqlalchemy import func
from app.models.spread_types import SpreadTypeModel  # Import the SpreadTypeModel
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.basic.mission_type import mission_types  # Import the mission_type data
from app.models.mission_type import MissionTypeModel  # Import here to avoid circular import
from app.models.mission import MissionModel  # Import MissionModel to fix NameError
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase to fix NameError
from datetime import datetime  # Import datetime to fix NameError
from app.services.websocket import ws_manager  # Import WebSocket manager
from app.models.notification import Notification  # Import Notification model to fix NameError

class NotificationSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
        
        
    @staticmethod
    async def get_all_notifications_by_user_id(
        db: AsyncSession,
        user_id: int
    ):
        # Obtém todas as notificações de um usuário pelo ID
        query = select(Notification).where(Notification.user == user_id)
        result = await db.execute(query)
        notifications = result.scalars().all()
        return notifications    
    
    @staticmethod
    async def get_status_by_id(
        db: AsyncSession,
        notification_id: int
    ):
        # Obtém o status de uma notificação pelo ID
        query = select(Notification.status).where(Notification.id == notification_id)
        result = await db.execute(query)
        status = result.scalar_one_or_none()
        if status is None:
            raise ValueError(f"Notification with id {notification_id} not found")
        return status
    
    @staticmethod
    async def notification_exists(
        db: AsyncSession,
        notification_id: int,
        user_id: int = None
    ):
        # Verifica se a notificação existe e, se user_id for fornecido, se pertence ao usuário
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if notification is None:
            return None
        if user_id is not None and notification.user != user_id:
            return None
        return notification
    
    @staticmethod
    async def modify_read_at_by_id(
        db: AsyncSession,
        notification_id: int
    ):
        # Modifica o campo read_at de uma notificação pelo ID
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if notification is None:
            raise ValueError(f"Notification with id {notification_id} not found")
        notification.read_at = datetime.now()
        try:
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Failed to update notification read_at: {str(e)}")
        
    @staticmethod
    async def modify_status_by_id(
        db: AsyncSession,
        notification_id: int,
        status_id: int
    ):
        
        # modifica o status de uma notificação pelo ID
        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()
        if notification is None:
            raise ValueError(f"Notification with id {notification_id} not found")
        notification.status = status_id
        try:
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Failed to update notification status: {str(e)}")
        
        
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: str,
        message: str,
        # outros campos que seu modelo tiver
    ):
        status_pending = await StatusSchemaBase.get_id_by_name(db=db, name="pending_confirmation")
        # 1. Salvar no banco
        notification = Notification(user=user_id, message=message, created_at=datetime.now(), status=status_pending)
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        

        return notification 
        
class NotificationSchema(NotificationSchemaBase):
    id: int
    user: int
    status: StatusSchemaBase
    created_at: datetime
    message: str
        
