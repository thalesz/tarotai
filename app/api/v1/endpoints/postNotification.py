from fastapi import APIRouter, Depends, Body, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.models.notification import Notification
from app.schemas.notification import NotificationSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.services.websocket import ws_manager
from pydantic import BaseModel, Field

router = APIRouter()

# ✅ Schema Pydantic para o corpo da requisição
class NotificationRequest(BaseModel):
    message: str = Field(..., description="Mensagem da notificação", example="Sua mensagem de notificação")

@router.post(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Enviar notificação para um usuário",
    description="""
    Envia uma notificação para um usuário específico com status "active" ou "pending_confirmation".  
    Cria a notificação no banco de dados e envia via WebSocket.
    """,
    responses={
        200: {
            "description": "Notificação enviada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Notificação enviada"
                    }
                }
            }
        },
        400: {"description": "Usuário não está apto a receber notificações"},
        404: {"description": "Usuário não encontrado"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def notify_user(
    user_id: int,
    payload: NotificationRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    Cria e envia uma notificação para um único usuário.

    - **user_id**: ID do usuário (na URL)
    - **payload.message**: Mensagem da notificação (via JSON body)
    """
    try:
        # Verifica se o usuário existe
        user_status = await UserSchemaBase.get_status_by_id(user_id, db)
        if user_status is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Usuário não encontrado"}
            )

        id_active = await StatusSchemaBase.get_id_by_name(db, "active")
        id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")

        if user_status != id_active and user_status != id_pending:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Usuário não está ativo ou não pode receber notificações"}
            )

        # Cria a notificação
        notification = await NotificationSchema.create_notification(db, user_id, payload.message)

        # Envia via WebSocket
        await ws_manager.send_notification(str(user_id), payload.message, notification.id)

        return {"detail": "Notificação enviada"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
